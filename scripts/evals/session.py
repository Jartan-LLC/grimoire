"""Run one sample: a fresh fixture repo, an isolated environment and one `claude -p` session.

Each setting below closes a leak seen in probe runs (Claude Code 2.1.309): without
`--strict-mcp-config` and ENABLE_CLAUDEAI_MCP_SERVERS=false the account's claude.ai
MCP servers loaded in some runs; without CLAUDE_CODE_DISABLE_AUTO_MEMORY every run got a
memory directory; the built-in `cc-plugin-*` plugins load unless disabled. A per-sample
venv keeps one session's `pip install` out of another's interpreter; it sees the
system's packages, so the tools a fixture's tests need (pytest) are there.
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
from dataclasses import dataclass

from . import cache, trace
from .arms import Arm
from .proc import CLAUDE, GIT, UV, run
from .suite import Case

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
    base: dict[str, str], checkout: pathlib.Path, sandbox: pathlib.Path
) -> dict[str, str]:
    """The session's environment: git isolated, this checkout off PATH, the sample's own venv and TMPDIR.

    CLAUDE* variables go too: the calling session's own (CLAUDECODE and the like)
    would tell the child it runs nested.
    """
    env = {k: v for k, v in git_env(base).items() if not k.startswith("CLAUDE")}
    for name in ("VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME"):
        env.pop(name, None)
    inside = str(checkout.resolve())
    path = [p for p in env.get("PATH", "").split(os.pathsep) if p and not p.startswith(inside)]
    env["PATH"] = os.pathsep.join([str(sandbox / "venv" / "bin"), *path])
    env["VIRTUAL_ENV"] = str(sandbox / "venv")
    env["TMPDIR"] = str(sandbox / "tmp")
    env["ENABLE_CLAUDEAI_MCP_SERVERS"] = "false"
    env["CLAUDE_CODE_DISABLE_AUTO_MEMORY"] = "1"
    return env


def claude_args(prompt: str, arm: Arm, model: str, budget_usd: float) -> list[str]:
    """The `claude` command line for one sample."""
    args = [
        CLAUDE, "-p", prompt,
        "--model", model,
        "--output-format", "stream-json", "--verbose", "--include-hook-events",
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


def new_commits(repo: pathlib.Path, env: dict[str, str], fixture_heads: list[str]) -> list[str]:
    """The full message of every commit the session added, on any branch, oldest first."""
    out = _git(repo, env, "log", "--all", "--reverse", "--format=%B%x1e", "--not", *fixture_heads)
    return [m.strip() for m in out.split("\x1e") if m.strip()]


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
        run(
            [UV, "venv", "-q", "--system-site-packages", str(sandbox / "venv")], env=env, check=True
        )
        out = sandbox / "trace.jsonl"
        timed_out = False
        with out.open("w") as handle:
            try:
                run(
                    claude_args(case.prompt, arm, spec.model, spec.budget_usd),
                    cwd=repo, env=sample_env(dict(os.environ), spec.checkout, sandbox),
                    stdout=handle, stderr=subprocess.STDOUT, timeout=TIMEOUT_S, check=False,
                )  # fmt: skip
            except subprocess.TimeoutExpired:
                timed_out = True
        text = out.read_text()
        parsed = trace.parse(trace.load(out), arm.plugins)
        private = [str(spec.checkout), str(case.path.parent.parent), str(spec.store / "samples")]
        reasons, spoiled = trace.classify(parsed, arm.plugins, spec.model, timed_out, private)
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
            usage=trace.usage(parsed) | {"tool_calls": len(parsed.tool_inputs)},
            spoiled=spoiled,
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
    rerun of the same screen resumes it.
    """
    sample_key = cache.key(
        case.hash(),
        f"{arm.name}:{arm.hash}:{spec.screen}:r{RUNNER}",
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
