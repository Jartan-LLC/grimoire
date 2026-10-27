"""Session setup: the parts that run no `claude` session."""

import json
import os
import pathlib
import subprocess

import pytest
from evals import cache, session
from evals.arms import Arm
from evals.proc import GIT, run
from evals.suite import Case, load_suite
from helpers import KEY, write_suite


def test_sample_env_isolates_git_drops_the_checkout_and_the_parent_session(
    tmp_path: pathlib.Path,
) -> None:
    checkout = tmp_path / "checkout"
    base = {
        "PATH": f"{checkout}/node_modules/.bin:/usr/bin",
        "GIT_DIR": "/elsewhere/.git",
        "VIRTUAL_ENV": "/venv",
        "CLAUDECODE": "1",
        "CLAUDE_EFFORT": "low",
        "CLAUDE_CODE_OAUTH_TOKEN": "token",
        "CLAUDE_CODE_USE_BEDROCK": "1",
        "HOME": "/home/u",
    }
    env = session.sample_env(base, checkout, tmp_path / "sandbox", tmp_path / "store")
    assert "GIT_DIR" not in env
    assert "CLAUDECODE" not in env
    assert "CLAUDE_EFFORT" not in env
    assert env["CLAUDE_CODE_OAUTH_TOKEN"] == base["CLAUDE_CODE_OAUTH_TOKEN"]
    assert env["CLAUDE_CODE_USE_BEDROCK"] == "1"
    assert env["GIT_CONFIG_GLOBAL"] == os.devnull
    assert env["PATH"] == f"{tmp_path}/sandbox/venv/bin:/usr/bin"
    assert env["VIRTUAL_ENV"] == f"{tmp_path}/sandbox/venv"
    assert env["TMPDIR"] == f"{tmp_path}/sandbox/tmp"
    assert env["ENABLE_CLAUDEAI_MCP_SERVERS"] == "false"
    assert env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] == "1"
    assert env["HOME"] == "/home/u"


def test_git_run_inside_an_arm_does_not_find_the_clone_holding_the_store(
    tmp_path: pathlib.Path,
) -> None:
    clone = tmp_path / "clone"
    run([GIT, "init", "-q", str(clone)], env=session.git_env(dict(os.environ)), check=True)
    store = clone / ".git" / "grimoire-evals"
    arm = store / "arms" / "old" / "plugins" / "gitwise"
    arm.mkdir(parents=True)
    env = session.sample_env(dict(os.environ), tmp_path / "checkout", tmp_path / "sandbox", store)
    found = run([GIT, "rev-parse", "--git-dir"], cwd=arm, env=env, capture_output=True, check=False)
    assert found.returncode != 0


def test_claude_args_load_every_arm_plugin_and_switch_off_the_builtins() -> None:
    arm = Arm("new", "h", {"gitwise": "/a/gitwise", "praxis": "/a/praxis"})
    args = session.claude_args("Do it.", arm, "claude-opus-5-5", 1.5, pathlib.Path("/s/debug.log"))
    assert args[1:3] == ["-p", "Do it."]
    assert args[args.index("--settings") + 1] == json.dumps(session.BUILTINS_OFF)
    assert args[args.index("--max-budget-usd") + 1] == "1.5"
    assert args[args.index("--debug-file") + 1] == "/s/debug.log"
    for flag in (
        "--strict-mcp-config", "--no-session-persistence", "--include-hook-events",
        "--forward-subagent-text",
    ):  # fmt: skip
        assert flag in args
    assert [args[i + 1] for i, a in enumerate(args) if a == "--plugin-dir"] == [
        "/a/gitwise",
        "/a/praxis",
    ]


def test_preloads_reads_only_the_skills_the_debug_log_says_an_agent_preloaded() -> None:
    log = (
        "2026-10-26T23:34:59.090Z [DEBUG] [Agent: praxis:general-reviewer] Preloaded skill "
        "'gitwise:github-conventions'\n"
        "2026-10-26T23:34:59.091Z [DEBUG] [Agent: praxis:general-reviewer] Preloaded skill "
        "'code-hygiene'\n"
        "2026-10-26T23:34:59.092Z [WARN] [Agent: praxis:test-reviewer] Warning: Skill "
        "'gone' specified in frontmatter was not found\n"
        "2026-10-26T23:34:59.093Z [DEBUG] Loaded skill 'other'\n"
    )
    assert session.preloads(log) == [
        ("praxis:general-reviewer", "gitwise:github-conventions"),
        ("praxis:general-reviewer", "code-hygiene"),
    ]


def test_build_fixture_commits_the_fixture_runs_build_and_new_commits_sees_only_the_sessions(
    tmp_path: pathlib.Path,
) -> None:
    case_dir = write_suite(tmp_path / "suite")
    (case_dir / "cases" / "c1" / "build.py").write_text(
        "import subprocess\nsubprocess.run(['git', 'checkout', '-q', '-b', 'feature/issue-42'], check=True)\n"
    )
    case = load_suite(case_dir).cases[0]
    env = session.git_env(dict(os.environ))
    repo = tmp_path / "repo"
    heads = session.build_fixture(case, repo, env)
    assert (repo / "app.py").read_text() == "x = 1\n"
    (repo / "app.py").write_text("x = 2\n")
    run([GIT, "stash", "-q"], cwd=repo, env=env, check=True)
    run(
        [GIT, "commit", "-q", "--allow-empty", "-m", "fix: the thing\n\nCloses #42"],
        cwd=repo,
        env=env,
        check=True,
    )
    assert session.new_commits(repo, env, heads) == ["fix: the thing\n\nCloses #42"]


def test_add_origin_pushes_every_fixture_branch_so_a_plain_push_works(
    tmp_path: pathlib.Path,
) -> None:
    case_dir = write_suite(tmp_path / "suite")
    (case_dir / "cases" / "c1" / "build.py").write_text(
        "import subprocess\n"
        "subprocess.run(['git', 'branch', 'release'], check=True)\n"
        "subprocess.run(['git', 'checkout', '-q', '-b', 'feature/issue-42'], check=True)\n"
        "subprocess.run(['git', 'commit', '-q', '--allow-empty', '-m', 'wip'], check=True)\n"
    )
    case = load_suite(case_dir).cases[0]
    env = session.git_env(dict(os.environ))
    repo = tmp_path / "repo"
    heads = session.build_fixture(case, repo, env)
    session.add_origin(repo, tmp_path / "origin.git", env)

    def git(*args: str) -> str:
        return run(
            [GIT, *args], cwd=repo, env=env, capture_output=True, text=True, check=True
        ).stdout

    branches = ["feature/issue-42", "main", "release"]
    for branch in branches:
        assert git("rev-parse", f"origin/{branch}") == git("rev-parse", branch)
    listed = git("ls-remote", "--heads", "origin").split()[1::2]
    assert listed == [f"refs/heads/{b}" for b in branches]
    git("commit", "-q", "--allow-empty", "-m", "fix: the thing")
    git("push", "-q")
    assert git("rev-parse", "origin/feature/issue-42") == git("rev-parse", "HEAD")
    assert session.new_commits(repo, env, heads) == ["fix: the thing"]


def test_add_origin_keeps_the_origin_build_made_with_a_branch_ahead_and_one_never_pushed(
    tmp_path: pathlib.Path,
) -> None:
    case_dir = write_suite(tmp_path / "suite")
    (case_dir / "cases" / "c1" / "build.py").write_text(
        "import subprocess\n"
        "def git(*args):\n"
        "    subprocess.run(['git', *args], check=True)\n"
        "git('init', '-q', '--bare', '../origin.git')\n"
        "git('remote', 'add', 'origin', '../origin.git')\n"
        "git('checkout', '-q', '-b', 'feature/issue-42')\n"
        "git('push', '-q', '-u', 'origin', 'main', 'feature/issue-42')\n"
        "git('commit', '-q', '--allow-empty', '-m', 'unpushed')\n"
        "git('branch', 'local-only')\n"
    )
    case = load_suite(case_dir).cases[0]
    env = session.git_env(dict(os.environ))
    repo = tmp_path / "repo"
    session.build_fixture(case, repo, env)
    session.add_origin(repo, tmp_path / "origin.git", env)

    def git(*args: str) -> str:
        return run(
            [GIT, *args], cwd=repo, env=env, capture_output=True, text=True, check=True
        ).stdout.strip()

    assert git("rev-list", "--count", "origin/feature/issue-42..feature/issue-42") == "1"
    listed = git("ls-remote", "--heads", "origin").split()[1::2]
    assert listed == ["refs/heads/feature/issue-42", "refs/heads/main"]


def test_a_commit_build_put_only_on_origin_is_not_the_sessions_once_pulled(
    tmp_path: pathlib.Path,
) -> None:
    case_dir = write_suite(tmp_path / "suite")
    (case_dir / "cases" / "c1" / "build.py").write_text(
        "import subprocess\n"
        "def git(*args, cwd=None):\n"
        "    subprocess.run(['git', *args], cwd=cwd, check=True)\n"
        "git('init', '-q', '--bare', '-b', 'main', '../origin.git')\n"
        "git('remote', 'add', 'origin', '../origin.git')\n"
        "git('push', '-q', '-u', 'origin', 'main')\n"
        "git('clone', '-q', '../origin.git', '../teammate')\n"
        "git('commit', '-q', '--allow-empty', '-m', 'teammate', cwd='../teammate')\n"
        "git('push', '-q', cwd='../teammate')\n"
    )
    case = load_suite(case_dir).cases[0]
    env = session.git_env(dict(os.environ))
    repo = tmp_path / "repo"
    heads = session.build_fixture(case, repo, env)
    heads += session.add_origin(repo, tmp_path / "origin.git", env)
    run([GIT, "pull", "-q", "--ff-only"], cwd=repo, env=env, check=True)
    run([GIT, "commit", "-q", "--allow-empty", "-m", "fix: mine"], cwd=repo, env=env, check=True)
    assert session.new_commits(repo, env, heads) == ["fix: mine"]


def test_sample_env_puts_the_gh_stub_first_and_drops_the_gh_login_only_for_a_case_that_asks(
    tmp_path: pathlib.Path,
) -> None:
    login = dict.fromkeys(session.GH_LOGIN, "x") | {"GH_CONFIG_DIR": "/home/u/.config/gh"}
    base = {"PATH": "/usr/bin"} | login
    sandbox = tmp_path / "sandbox"
    plain = session.sample_env(base, tmp_path, sandbox, tmp_path / "store")
    assert plain["PATH"] == f"{sandbox}/venv/bin:/usr/bin"
    assert {k: plain[k] for k in login} == login
    stubbed = session.sample_env(base, tmp_path, sandbox, tmp_path / "store", gh_stub=True)
    assert stubbed["PATH"] == f"{sandbox}/bin:{sandbox}/venv/bin:/usr/bin"
    assert stubbed["GH_CONFIG_DIR"] == f"{sandbox}/gh-config"
    assert not any(name in stubbed for name in session.GH_LOGIN)


def limited_sample(reason: str) -> cache.Sample:
    return cache.Sample("k", "c1", "new", 0, {}, False, [reason], [], "", {}, {})


def test_limited_reads_the_apis_limit_messages() -> None:
    assert session.limited(
        limited_sample(
            "session ended in error: success: API Error: Server is temporarily limiting requests"
        )
    )
    assert session.limited(limited_sample("session ended in error: API Error: 529 overloaded"))
    assert not session.limited(limited_sample("MCP servers loaded: [...]"))


def test_the_breaker_trips_after_a_streak_and_a_success_resets_it() -> None:
    breaker = session.Breaker()
    for _ in range(session.BREAKER - 1):
        breaker.record(limited=True)
    breaker.record(limited=False)
    breaker.record(limited=True)
    assert not breaker.tripped.is_set()
    for _ in range(session.BREAKER - 1):
        breaker.record(limited=True)
    assert breaker.tripped.is_set()


def test_a_tripped_breaker_returns_not_run_without_a_session(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = load_suite(write_suite(tmp_path / "suite")).cases[0]
    spec = session.Spec("m", "v", 1.0, tmp_path, tmp_path / "store")

    def no_session(*_: object) -> None:
        raise AssertionError("a tripped breaker must not start a session")

    monkeypatch.setattr(session, "_session", no_session)
    breaker = session.Breaker()
    breaker.tripped.set()
    sample = session.run_sample(case, Arm("new", "h", {}), 0, spec, breaker)
    assert not sample.valid
    assert sample.reasons[0].startswith("not run:")
    assert cache.load(spec.store, sample.key) is None


def test_preflight_stops_when_the_sample_venv_cannot_import_pytest(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def no_pytest(args: list[str], **_: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args, 1 if args[-1] == "import pytest" else 0, stdout="/opt/python3.12/bin/python3\n"
        )

    monkeypatch.setattr(session, "run", no_pytest)
    with pytest.raises(
        SystemExit, match=r"built on /opt/python3\.12/bin/python3, which has no pytest"
    ):
        session.preflight()


def test_a_samples_key_holds_its_arms_name_screen_and_runner(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case = load_suite(write_suite(tmp_path / "suite")).cases[0]
    breaker = session.Breaker()
    breaker.tripped.set()

    def key(arm: str, screen: str) -> str:
        spec = session.Spec("m", "v", 1.0, tmp_path, tmp_path / "store", screen)
        return session.run_sample(case, Arm(arm, "h", {}), 0, spec, breaker).key

    keys = {key("old", "s1"), key("new", "s1"), key("old", "s2")}
    monkeypatch.setattr(session, "RUNNER", session.RUNNER + 1)
    keys.add(key("old", "s1"))
    assert len(keys) == 4


def test_private_paths_from_a_worktree_hold_every_working_tree_of_the_clone(
    tmp_path: pathlib.Path,
) -> None:
    env = session.git_env(dict(os.environ))
    clone, worktree, sibling = tmp_path / "clone", tmp_path / "worktree", tmp_path / "sibling"
    run([GIT, "init", "-q", "-b", "main", str(clone)], env=env, check=True)
    run([GIT, "commit", "-q", "--allow-empty", "-m", "start"], cwd=clone, env=env, check=True)
    for tree in (worktree, sibling):
        run([GIT, "worktree", "add", "-q", "--detach", str(tree)], cwd=clone, env=env, check=True)
    case = load_suite(write_suite(worktree / "tests" / "evals" / "x")).cases[0]
    store = clone.resolve() / ".git" / "grimoire-evals"
    spec = session.Spec("m", "v", 1.0, worktree.resolve(), store)
    assert session.private_paths(case, spec) == [
        str(worktree.resolve()),
        str(clone.resolve()),
        str(sibling.resolve()),
        str(worktree / "tests" / "evals" / "x"),
        str(store / "samples"),
    ]


def test_the_remote_runner_is_in_a_remote_cases_key_only(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    local = load_suite(write_suite(tmp_path / "local")).cases[0]
    remote = load_suite(write_suite(tmp_path / "remote", key="remote = true\n" + KEY)).cases[0]
    breaker = session.Breaker()
    breaker.tripped.set()
    spec = session.Spec("m", "v", 1.0, tmp_path, tmp_path / "store", "s1")

    def key(case: Case) -> str:
        return session.run_sample(case, Arm("old", "h", {}), 0, spec, breaker).key

    before = key(local), key(remote)
    assert before[0] == cache.key(local.pinned(), f"old:h:s1:r{session.RUNNER}", "m", "v", 0)
    monkeypatch.setattr(session, "REMOTE_RUNNER", session.REMOTE_RUNNER + 1)
    assert key(local) == before[0]
    assert key(remote) != before[1]


def test_a_case_changed_on_disk_after_loading_is_excluded_before_its_session(
    tmp_path: pathlib.Path,
) -> None:
    root = write_suite(tmp_path / "suite")
    case = load_suite(root).cases[0]
    (root / "cases" / "c1" / "fixture" / "app.py").write_text("x = 2\n")
    spec = session.Spec("m", "v", 1.0, tmp_path, tmp_path / "store")
    sample, _ = session._session(case, Arm("old", "h", {}), 0, spec, "k")  # pyright: ignore[reportPrivateUsage]
    assert not sample.valid
    assert "changed on disk" in sample.reasons[0]
