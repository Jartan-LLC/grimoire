"""Run one sample: a fresh fixture repo, an isolated environment and one `claude -p` session.

Each setting below closes a leak seen in probe runs (Claude Code 2.1.309): without
`--strict-mcp-config` and ENABLE_CLAUDEAI_MCP_SERVERS=false the account's claude.ai
MCP servers loaded in some runs; without CLAUDE_CODE_DISABLE_AUTO_MEMORY every run got a
memory directory; the built-in `cc-plugin-*` plugins load unless disabled. A per-sample
venv sees the base interpreter's packages, so the tools a fixture's tests need (pytest)
come from there, and `python3 -m pip install` stays in the sample. The venv has no pip of
its own: a bare `pip install` reaches the base interpreter, which later samples see.

From probe runs on 2.1.311: `--forward-subagent-text` sends a subagent's skill text, which
the stream holds back by default, and the debug log names each skill an agent's
frontmatter preloads; only those lines are kept, as the sample's `preloads`.
"""

import json
import os
import pathlib
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from dataclasses import asdict, dataclass

from . import cache, trace
from .arms import Arm
from .proc import CLAUDE, GIT, UV, run
from .suite import Case, Reply

BUILTINS_OFF = {
    "enabledPlugins": {
        "cc-plugin-agents-md@builtin": False,
        "cc-plugin-telemetry@builtin": False,
        "cc-plugin-plugin-authoring@builtin": False,
    }
}
TIMEOUT_S = 1800
RETRIES = 3
BACKOFF_S = 30  # the first wait after the API limits requests; it doubles per retry
BREAKER = 3  # samples in a row still limited after every retry stop the run
LIMITED = re.compile(r"(?i)limiting requests|usage limit|rate limit|overloaded|\b(429|529)\b")
# Part of every sample's key: bump it when a change to the session setup changes what a
# session can do, so no sample drawn under the old setup is reused.
RUNNER = 2
# Part of a remote case's sample key only: bump it when a change to the gh stub or to the
# remote setup changes what a remote session can do, so only remote cases draw again.
REMOTE_RUNNER = 2
PRELOADED = re.compile(r"\[Agent: ([^\]]+)\] Preloaded skill '([^']+)'")
GH_STUB = pathlib.Path(__file__).with_name("gh_stub.py")
REPLIES = "replies.json"
GH_LOGIN = ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN", "GH_HOST")
SSH_AGENT = ("SSH_AUTH_SOCK", "SSH_AGENT_PID")


@dataclass(frozen=True)
class Spec:
    """What every sample of one run shares."""

    model: str
    version: str
    budget_usd: float
    checkout: pathlib.Path
    store: pathlib.Path
    screen: str = ""


def git_env(base: dict[str, str]) -> dict[str, str]:
    """`base` with every GIT_* variable dropped and no user or system git config."""
    env = {k: v for k, v in base.items() if not k.startswith("GIT_")}
    env |= {
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_AUTHOR_NAME": "Fixture",
        "GIT_AUTHOR_EMAIL": "fixture@example.com",
        "GIT_COMMITTER_NAME": "Fixture",
        "GIT_COMMITTER_EMAIL": "fixture@example.com",
    }
    return env


def sample_env(
    base: dict[str, str],
    checkout: pathlib.Path,
    sandbox: pathlib.Path,
    store: pathlib.Path,
    gh_stub: bool = False,
) -> dict[str, str]:
    """The session's environment: git isolated, this checkout off PATH, the sample's own venv and TMPDIR.

    Git run inside an arm stops at `store`, so it does not find the clone whose git
    directory holds the store.

    CLAUDE* variables go too: the calling session's own (CLAUDECODE and the like)
    would tell the child it runs nested, and others (CLAUDE_EFFORT) would change it.
    The login ones stay, so a token, config-dir, Bedrock or Vertex login still works.
    With `gh_stub`, the sandbox's `bin/` comes first, so its `gh` answers every call, and
    the user's gh login and SSH agent are gone (gh's token variables and the SSH agent's
    dropped, GH_CONFIG_DIR an empty `gh-config/`), so neither the real `gh` run by its
    path nor a push to a remote the session adds reaches the user's account.
    """
    env = {
        k: v
        for k, v in git_env(base).items()
        if not k.startswith("CLAUDE")
        or k in ("CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CONFIG_DIR")
        or k.startswith("CLAUDE_CODE_USE_")
    }
    for name in ("VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME"):
        env.pop(name, None)
    inside = str(checkout.resolve())
    path = [p for p in env.get("PATH", "").split(os.pathsep) if p and not p.startswith(inside)]
    first = [str(sandbox / "bin")] if gh_stub else []
    env["PATH"] = os.pathsep.join([*first, str(sandbox / "venv" / "bin"), *path])
    env["VIRTUAL_ENV"] = str(sandbox / "venv")
    env["TMPDIR"] = str(sandbox / "tmp")
    env["ENABLE_CLAUDEAI_MCP_SERVERS"] = "false"
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    env["GIT_CEILING_DIRECTORIES"] = str(store)
    if gh_stub:
        for name in (*GH_LOGIN, *SSH_AGENT):
            env.pop(name, None)
        env["GH_CONFIG_DIR"] = str(sandbox / "gh-config")
    return env


def claude_args(
    prompt: str, arm: Arm, model: str, budget_usd: float, debug_log: pathlib.Path
) -> list[str]:
    """The `claude` command line for one sample, writing its debug log to `debug_log`."""
    args = [
        CLAUDE, "-p", prompt,
        "--model", model,
        "--output-format", "stream-json", "--verbose", "--include-hook-events",
        "--forward-subagent-text", "--debug-file", str(debug_log),
        "--setting-sources", "project",
        "--settings", json.dumps(BUILTINS_OFF),
        "--strict-mcp-config",
        "--no-session-persistence",
        "--dangerously-skip-permissions",
        "--max-budget-usd", f"{budget_usd:g}",
    ]  # fmt: skip
    for directory in arm.plugins.values():
        args += ["--plugin-dir", directory, "--add-dir", directory]
    return args


def preloads(debug_log: str) -> list[tuple[str, str]]:
    """The (agent, skill) pairs a session's debug log says were preloaded, in its order."""
    return [(m[1], m[2]) for m in PRELOADED.finditer(debug_log)]


def _git(repo: pathlib.Path, env: dict[str, str], *args: str) -> str:
    return run([GIT, *args], cwd=repo, env=env, capture_output=True, text=True, check=True).stdout


def build_fixture(case: Case, repo: pathlib.Path, env: dict[str, str]) -> list[str]:
    """Copy the case's fixture into `repo`, commit it, run its `build.py`; return every ref's commit.

    `build.py` runs inside the repo after the first commit, so it can add history,
    branches or files; it must stay offline and use only python3.
    """
    fixture = case.path / "fixture"
    if fixture.is_dir():
        shutil.copytree(fixture, repo, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    else:
        repo.mkdir(parents=True)
    _git(repo, env, "init", "-q", "-b", "main")
    _git(repo, env, "add", "-A")
    _git(repo, env, "commit", "-q", "--allow-empty", "-m", "chore: start the fixture")
    build = case.path / "build.py"
    if build.is_file():
        run([sys.executable, "-I", str(build)], cwd=repo, env=env, check=True)
    return _git(repo, env, "rev-parse", "--all").split()


def add_origin(repo: pathlib.Path, origin: pathlib.Path, env: dict[str, str]) -> list[str]:
    """Make `origin` a bare repository holding every branch and tag of `repo`, each branch tracking it.

    An `origin` the case's `build.py` made is kept as it left it, so a case can start
    with a branch ahead of, behind or missing from it. Either way `origin/HEAD` names
    origin's default branch, as in a clone, unless `repo` has one already or origin's
    HEAD names no branch it holds. Returns the commit of each of origin's refs: one
    `repo` has not fetched is the fixture's, not the session's, once pulled.
    """
    if "origin" not in _git(repo, env, "remote").split():
        run([GIT, "init", "-q", "--bare", "-b", "main", str(origin)], env=env, check=True)
        _git(repo, env, "remote", "add", "origin", str(origin))
        _git(repo, env, "push", "-q", "-u", "origin", "--all")
        _git(repo, env, "push", "-q", "origin", "--tags")
    head = [GIT, "symbolic-ref", "-q", "refs/remotes/origin/HEAD"]
    if run(head, cwd=repo, env=env, capture_output=True, check=False).returncode != 0:
        # Fails, leaving none, when origin's HEAD names no branch it holds.
        set_head = [GIT, "remote", "set-head", "origin", "-a"]
        run(set_head, cwd=repo, env=env, capture_output=True, check=False)
    return [line.split()[0] for line in _git(repo, env, "ls-remote", "origin").splitlines()]


def install_gh(sandbox: pathlib.Path, replies: tuple[Reply, ...]) -> None:
    """Put the recording `gh` stub in `sandbox/bin`, answering with `replies`, its log in `sandbox/gh`.

    `sandbox/gh-config` is made empty, for the session's GH_CONFIG_DIR.
    """
    (sandbox / "bin").mkdir()
    (sandbox / "gh-config").mkdir()
    (sandbox / "gh").mkdir()
    stub = sandbox / "bin" / "gh"
    stub.write_text("#!/usr/bin/env -S python3 -I\n" + GH_STUB.read_text())
    stub.chmod(0o755)
    replies_json = json.dumps([asdict(r) for r in replies])
    (sandbox / "gh" / REPLIES).write_text(replies_json)
    (sandbox / "gh" / "calls.jsonl").touch()


def gh_calls(sandbox: pathlib.Path) -> list[dict[str, object]]:
    """The calls the sandbox's `gh` stub recorded, in order; a line that is not JSON is skipped."""
    log = sandbox / "gh" / "calls.jsonl"
    return trace.load_text(log.read_text()) if log.is_file() else []


def new_commits(repo: pathlib.Path, env: dict[str, str], fixture_heads: list[str]) -> list[str]:
    """The full message of every commit the session added, on any branch, oldest first.

    A stash it left behind is not one: its "WIP on" commits are git's text, not the agent's.
    A head `repo` does not hold, on an origin it never fetched from, is skipped.
    """
    out = _git(
        repo, env, "log", "--ignore-missing", "--exclude=refs/stash", "--all", "--reverse",
        "--format=%B%x1e", "--not", *fixture_heads,
    )  # fmt: skip
    return [m.strip() for m in out.split("\x1e") if m.strip()]


def private_paths(case: Case, spec: Spec, sandbox: pathlib.Path) -> list[str]:
    """The paths a session must not name: the checkout, every working tree of its clone, suite and samples.

    The clone's other working trees, the main one and each sibling worktree, hold the
    same suite and its answers. A remote case's session must not name the `gh` stub's
    directory in `sandbox`, nor its `replies.json` by any path: a reply's `match` can show
    what the case wants the agent to send.
    """
    listed = run(
        [GIT, "worktree", "list", "--porcelain"],
        cwd=spec.checkout, capture_output=True, text=True, check=True,
    ).stdout  # fmt: skip
    trees = [
        line.removeprefix("worktree ")
        for line in listed.splitlines()
        if line.startswith("worktree ")
    ]
    stub = [str(sandbox / "gh"), REPLIES] if case.remote else []
    return list(
        dict.fromkeys(
            [
                str(spec.checkout), *trees, str(case.path.parent.parent),
                str(spec.store / "samples"), *stub,
            ]
        )
    )  # fmt: skip


def _session(
    case: Case, arm: Arm, index: int, spec: Spec, sample_key: str
) -> tuple[cache.Sample, str]:
    """Run one session in a fresh sandbox and collect what it left."""
    sandbox = pathlib.Path(tempfile.mkdtemp(prefix="grimoire-eval-"))
    try:
        (sandbox / "tmp").mkdir()
        repo = sandbox / "repo"
        env = git_env(dict(os.environ))
        heads = build_fixture(case, repo, env)
        if case.hash() != case.pinned():
            reason = "the case changed on disk during the run; rerun once the checkout is settled"
            sample = cache.Sample(
                sample_key, case.id, arm.name, index, arm.plugins, False, [reason], [], "", {}, {}
            )
            return sample, ""
        if case.remote:
            heads += add_origin(repo, sandbox / "origin.git", env)
            install_gh(sandbox, case.gh)
        run(
            [UV, "venv", "-q", "--system-site-packages", str(sandbox / "venv")], env=env, check=True
        )
        out = sandbox / "trace.jsonl"
        debug_log = sandbox / "debug.log"
        timed_out = False
        session_env = sample_env(
            dict(os.environ), spec.checkout, sandbox, spec.store, gh_stub=case.remote
        )
        with out.open("w") as handle:
            try:
                run(
                    claude_args(case.prompt, arm, spec.model, spec.budget_usd, debug_log),
                    cwd=repo, env=session_env,
                    stdout=handle, stderr=subprocess.STDOUT, timeout=TIMEOUT_S, check=False,
                )  # fmt: skip
            except subprocess.TimeoutExpired:
                timed_out = True
        text = out.read_text()
        loaded = preloads(debug_log.read_text(errors="replace")) if debug_log.is_file() else []
        parsed = trace.parse(trace.load(out), arm.plugins, loaded)
        private = private_paths(case, spec, sandbox)
        reasons, spoiled = trace.classify(
            parsed, arm.plugins, spec.model, timed_out, private, arms=str(spec.store / "arms")
        )
        result = parsed.result or {}
        files = {p: (repo / p).read_text() for p in case.files() if (repo / p).is_file()}
        sample = cache.Sample(
            key=sample_key,
            case=case.id,
            arm=arm.name,
            index=index,
            plugins=arm.plugins,
            valid=not reasons,
            reasons=reasons,
            commits=new_commits(repo, env, heads),
            final=str(result.get("result", "")),
            files=files,
            usage=trace.usage(parsed)
            | {
                "tool_calls": len(parsed.tool_inputs),
                "agents": [[r.agent, r.model] for r in parsed.reports],
            },
            spoiled=spoiled,
            collected=case.files(),
            preloads=[list(p) for p in loaded],
            gh=gh_calls(sandbox) if case.remote else None,
        )
        return sample, text
    finally:
        shutil.rmtree(sandbox, ignore_errors=True)


class Breaker:
    """Stops a run once the API keeps limiting requests, so the rest are not burned on failures.

    Shared by the run's worker threads: after BREAKER samples in a row are still
    limited once their retries are spent, it trips, and every sample not yet started
    returns at once as not run. A sample that succeeds resets the count.
    """

    def __init__(self) -> None:
        """An untripped breaker with no limited samples counted."""
        self._lock = threading.Lock()
        self._streak = 0
        self.tripped = threading.Event()

    def record(self, limited: bool) -> None:
        """Count one finished sample."""
        with self._lock:
            self._streak = self._streak + 1 if limited else 0
            if self._streak >= BREAKER:
                self.tripped.set()


def limited(sample: cache.Sample) -> bool:
    """Whether the sample was excluded because the API limited requests."""
    return not sample.valid and any(LIMITED.search(reason) for reason in sample.reasons)


def preflight() -> None:
    """Stop before any session when a sample venv would not have pytest to run fixture tests."""
    with tempfile.TemporaryDirectory(prefix="grimoire-eval-") as scratch:
        venv = pathlib.Path(scratch) / "venv"
        run([UV, "venv", "-q", "--system-site-packages", str(venv)], check=True)
        python = str(venv / "bin" / "python")
        found = run([python, "-c", "import pytest"], capture_output=True)
        base = run(
            [python, "-c", "import sys; print(sys._base_executable)"],
            capture_output=True,
            text=True,
        ).stdout.strip()
    if found.returncode != 0:
        raise SystemExit(
            f"sample venvs are built on {base or 'the base Python'}, which has no pytest, and "
            "fixture tests need it: install pytest into that interpreter (this checkout's .venv "
            "does not count)"
        )


def run_sample(
    case: Case, arm: Arm, index: int, spec: Spec, breaker: Breaker | None = None
) -> cache.Sample:
    """The cached sample for (case, arm, model, version, index), running the session if missing.

    An excluded sample (the infrastructure failed: a usage limit, a leaked setting, a
    session that reached the suite's files) is retried up to RETRIES times and kept
    for its reasons, never reused: the next run retries it too. When the API limits
    requests, each retry first waits, BACKOFF_S doubling, and `breaker` stops the run
    once limits persist; a sample not started then is returned as not run and not
    saved. A sample the arm spoiled is valid and counts. The arm's name is part of the
    key, so `new` never reuses `old`'s sessions even when their plugins are identical,
    and `spec.screen` is too, so each screen draws fresh samples for both arms while a
    rerun of the same screen resumes it. RUNNER is in every key, REMOTE_RUNNER in a
    remote case's only.
    """
    runner = f"r{RUNNER}" + (f":g{REMOTE_RUNNER}" if case.remote else "")
    sample_key = cache.key(
        case.pinned(),
        f"{arm.name}:{arm.hash}:{spec.screen}:{runner}",
        spec.model,
        spec.version,
        index,
    )
    if (cached := cache.load(spec.store, sample_key)) is not None and cached.valid:
        return cached
    if breaker is not None and breaker.tripped.is_set():
        reason = "not run: the API kept limiting requests; rerun later to resume"
        return cache.Sample(
            sample_key, case.id, arm.name, index, arm.plugins, False, [reason], [], "", {}, {}
        )
    sample, text = _session(case, arm, index, spec, sample_key)
    for attempt in range(RETRIES):
        if sample.valid:
            break
        if limited(sample):
            time.sleep(BACKOFF_S * 2**attempt)
        sample, text = _session(case, arm, index, spec, sample_key)
    if breaker is not None:
        breaker.record(limited(sample))
    cache.save(spec.store, sample, text)
    return sample
