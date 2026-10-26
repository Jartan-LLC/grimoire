"""Session setup: the parts that run no `claude` session."""

import json
import os
import pathlib
import subprocess

import pytest
from evals import cache, session
from evals.arms import Arm
from evals.proc import GIT, run
from evals.suite import load_suite
from helpers import write_suite


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
    env = session.sample_env(base, checkout, tmp_path / "sandbox")
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


def test_claude_args_load_every_arm_plugin_and_switch_off_the_builtins() -> None:
    arm = Arm("new", "h", {"gitwise": "/a/gitwise", "praxis": "/a/praxis"})
    args = session.claude_args("Do it.", arm, "claude-opus-5-5", 1.5)
    assert args[1:3] == ["-p", "Do it."]
    assert args[args.index("--settings") + 1] == json.dumps(session.BUILTINS_OFF)
    assert args[args.index("--max-budget-usd") + 1] == "1.5"
    for flag in ("--strict-mcp-config", "--no-session-persistence", "--include-hook-events"):
        assert flag in args
    assert [args[i + 1] for i, a in enumerate(args) if a == "--plugin-dir"] == [
        "/a/gitwise",
        "/a/praxis",
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
