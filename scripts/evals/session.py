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

import contextlib
import json
import os
import pathlib
import re
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import threading
import time
from collections.abc import Sequence
from dataclasses import asdict, dataclass, field, replace
from typing import TextIO, cast

from . import cache, trace
from .arms import Arm
from .gh_stub import REPLIES, TEMP_ROOTS
from .proc import CLAUDE, GIT, UV, run, start
from .suite import FILES, TIMEOUT_S, Case, Reply, glob_match, python_cache

BUILTINS_OFF = {
    "enabledPlugins": {
        "cc-plugin-agents-md@builtin": False,
        "cc-plugin-telemetry@builtin": False,
        "cc-plugin-plugin-authoring@builtin": False,
    }
}
# A wakeup or cron job the agent schedules for itself keeps `claude -p` alive until it
# fires (20 minutes in #160), and no task under test needs one.
SCHEDULERS = ("ScheduleWakeup", "CronCreate")
RETRIES = 3
BACKOFF_S = 30  # the first wait after the API limits requests; it doubles per retry
BREAKER = 3  # samples in a row still limited after every retry stop the run
LIMITED = re.compile(r"(?i)limiting requests|usage limit|rate limit|overloaded|\b(429|529)\b")
# Part of every sample's key: bump it when a change to the session setup could change how a
# session does a task under test, so no sample drawn under the old setup is reused.
RUNNER = 2
# Part of a remote case's sample key only: bump it when a change to the gh stub or to the
# remote setup changes what a remote session can do, so only remote cases draw again.
REMOTE_RUNNER = 3
PRELOADED = re.compile(r"\[Agent: ([^\]]+)\] Preloaded skill '([^']+)'")
GH_STUB = pathlib.Path(__file__).with_name("gh_stub.py")
# The stub's replies and log, private: no path the session is given (repo, venv, bin, gh-config,
# tmp) may lie under it, or using that path would exclude the sample.
GH_STATE = "gh-stub"
GH_LOGIN = ("GH_TOKEN", "GITHUB_TOKEN", "GH_ENTERPRISE_TOKEN", "GITHUB_ENTERPRISE_TOKEN", "GH_HOST")
SSH_AGENT = ("SSH_AUTH_SOCK", "SSH_AGENT_PID")
# Set as GH_TOKEN, so the real `gh` uses no token of the user's; the stub reads no token.
STUB_TOKEN = "grimoire-eval-stub"  # noqa: S105 -- a dummy that authenticates nothing
# A temp directory the stub reads besides the runner's, which TMPDIR can move elsewhere.
SHARED_TMP = pathlib.Path("/tmp")  # noqa: S108 -- read for a body file, never written
VERIFY_TIMEOUT_S = 60
NOT_STARTED = 127  # a shell's exit code for a command it cannot find


@dataclass(frozen=True)
class Spec:
    """What every sample of one run shares; `env` is the suite's."""

    model: str
    version: str
    budget_usd: float
    checkout: pathlib.Path
    store: pathlib.Path
    screen: str = ""
    timeout_s: float = TIMEOUT_S
    env: dict[str, str] = field(default_factory=dict[str, str])


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


def claude_env(base: dict[str, str]) -> dict[str, str]:
    """`base` without CLAUDE* variables but the login ones (`sample_env` says why)."""
    return {
        k: v
        for k, v in base.items()
        if not k.startswith("CLAUDE")
        or k in ("CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CONFIG_DIR")
        or k.startswith("CLAUDE_CODE_USE_")
    }


def sample_env(  # noqa: PLR0913 -- `suite_env` is apart from `base`: it is set after the strip
    base: dict[str, str],
    checkout: pathlib.Path,
    sandbox: pathlib.Path,
    store: pathlib.Path,
    *,
    gh_stub: bool = False,
    suite_env: dict[str, str] | None = None,
) -> dict[str, str]:
    """The session's environment: git isolated, this checkout off PATH, the sample's own venv and TMPDIR.

    Git run inside an arm stops at `store`, so it does not find the clone whose git
    directory holds the store. GRIMOIRE_EVALS_STORE goes, but GIT_CEILING_DIRECTORIES
    holds the store's path, so a path built from it gets past the check on each tool
    call's paths.

    CLAUDE* variables go too: the calling session's own (CLAUDECODE and the like)
    would tell the child it runs nested, and others (CLAUDE_EFFORT) would change it.
    The login ones stay, so a token, config-dir, Bedrock or Vertex login still works.
    The suite's `suite_env` is set after that, and the runner's own settings after it.
    With `gh_stub`, the sandbox's `bin/` comes first, so its `gh` answers every call. For
    the real `gh` run by its path: gh's token and host variables are dropped, GH_TOKEN is
    set to a dummy, which gh sends to github.com in place of a token from the OS keyring,
    and GH_CONFIG_DIR is an empty `gh-config/`. The stub's TEMP_ROOTS are this process's
    temp directory and `/tmp` when it exists, where an agent may write a body file by its
    path. For git: GIT_ALLOW_PROTOCOL=file refuses every transport but a local path, so git
    reaches no https, ssh or git URL, and the SSH agent's variables are dropped. These
    controls hold only while the session keeps this environment: one that unsets
    GIT_ALLOW_PROTOCOL can reach the network with a key under HOME, as one that unsets
    the gh variables reaches the user's gh login.
    """
    env = claude_env(git_env(base)) | (suite_env or {})
    for name in ("VIRTUAL_ENV", "PYTHONPATH", "PYTHONHOME", cache.STORE):
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
        env["GH_TOKEN"] = STUB_TOKEN
        env["GH_CONFIG_DIR"] = str(sandbox / "gh-config")
        temps = (pathlib.Path(tempfile.gettempdir()), SHARED_TMP)
        resolved = (str(t.resolve()) for t in temps if t.is_dir())
        env[TEMP_ROOTS] = os.pathsep.join(dict.fromkeys(resolved))
        env["GIT_ALLOW_PROTOCOL"] = "file"
    return env


def claude_args(
    prompt: str | None, arm: Arm, model: str, budget_usd: float, debug_log: pathlib.Path
) -> list[str]:
    """The `claude` command line for one sample, writing its debug log to `debug_log`.

    With no `prompt`, the session reads its messages from stdin as stream-json (`converse`).
    """
    args = [
        CLAUDE, "-p", *([] if prompt is None else [prompt]),
        "--model", model,
        "--output-format", "stream-json", "--verbose", "--include-hook-events",
        "--forward-subagent-text", "--debug-file", str(debug_log),
        "--setting-sources", "project",
        "--settings", json.dumps(BUILTINS_OFF),
        "--strict-mcp-config",
        "--no-session-persistence",
        "--dangerously-skip-permissions",
        "--disallowedTools", *SCHEDULERS,
        "--max-budget-usd", f"{budget_usd:g}",
    ]  # fmt: skip
    for directory in arm.plugins.values():
        args += ["--plugin-dir", directory, "--add-dir", directory]
    if prompt is None:
        args += ["--input-format", "stream-json"]
    return args


def _message(text: str) -> str:
    return json.dumps({"type": "user", "message": {"role": "user", "content": text}}) + "\n"


def _event(line: str) -> dict[str, object]:
    """A trace line's event; empty for a line that is no JSON object (stderr noise)."""
    try:
        event = json.loads(line)
    except json.JSONDecodeError:
        return {}
    return cast("dict[str, object]", event) if isinstance(event, dict) else {}


def converse(  # noqa: PLR0913 -- where it runs, what it writes and how long it may take are apart
    args: list[str],
    messages: Sequence[str],
    *,
    cwd: pathlib.Path,
    env: dict[str, str],
    out: TextIO,
    timeout_s: float,
) -> tuple[bool, str]:
    """Run a session whose turns are `messages`, sent on stdin, writing its output to `out`.

    Each message after the first goes in once the turn before has ended in a `result`
    event: one sent sooner joins the turn in progress. Stdin closes right after the
    last, as a session still runs the messages it got before the close, and the
    background tasks they start. A turn that starts a background task, such as a
    subagent the main thread spawns, emits its `result` only when the session ends
    (probe on 2.1.314), so no later turn can follow it: the runner then sends no more.
    A session that ends before it got every message, or before each turn it got has
    its `result`, was cut short too. Returns whether the session timed out, and why its
    turns did not all run, or "".
    """
    session = start(
        args, cwd=cwd, env=env,
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )  # fmt: skip
    stdin, stdout = cast("TextIO", session.stdin), cast("TextIO", session.stdout)
    expired = threading.Event()

    def expire() -> None:
        expired.set()
        session.kill()

    timer = threading.Timer(timeout_s, expire)
    timer.start()
    pending, sent, results, cut_short = list(messages), 0, 0, ""

    def send() -> None:
        nonlocal sent
        try:
            stdin.write(_message(pending.pop(0)))
            stdin.flush()
            sent += 1
            if not pending:
                stdin.close()
        except OSError:  # the session has ended: nothing more can reach it
            pending.clear()

    def stop() -> None:
        pending.clear()
        with contextlib.suppress(OSError):  # the session has ended already
            stdin.close()

    try:
        send()
        for line in stdout:
            out.write(line)
            event = _event(line)
            if event.get("type") == "result":
                results += 1
            if not pending:
                continue
            if event.get("subtype") == "task_started" and event.get("is_backgrounded") is True:
                cut_short = (
                    f"turn {sent} started a background task, whose result comes only when the "
                    f"session ends, so turn {sent + 1} of {len(messages)} was not sent"
                )
                stop()
            elif event.get("type") == "result":
                send()
        session.wait()
    finally:
        timer.cancel()
        if session.poll() is None:  # the loop raised: stop the session rather than leave it
            session.kill()
            session.wait()
    if not cut_short and not expired.is_set() and min(sent, results) < len(messages):
        cut_short = (
            f"the session ended after {results} of {len(messages)} turns had their result, "
            f"{sent} sent"
        )
    return expired.is_set(), cut_short


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
    `repo` has not fetched is the fixture's, not the session's, once pulled. An origin
    at a network URL fails at once, reaching no network and waiting on no prompt. The
    pushes that fill a new origin skip the fixture's pre-push hook, which is there for
    the session's pushes.
    """
    env = {**env, "GIT_ALLOW_PROTOCOL": "file", "GIT_TERMINAL_PROMPT": "0"}
    if "origin" not in _git(repo, env, "remote").split():
        run([GIT, "init", "-q", "--bare", "-b", "main", str(origin)], env=env, check=True)
        _git(repo, env, "remote", "add", "origin", str(origin))
        _git(repo, env, "push", "-q", "--no-verify", "-u", "origin", "--all")
        _git(repo, env, "push", "-q", "--no-verify", "origin", "--tags")
    head = [GIT, "symbolic-ref", "-q", "refs/remotes/origin/HEAD"]
    if run(head, cwd=repo, env=env, capture_output=True, check=False).returncode != 0:
        # Fails, leaving none, when origin's HEAD names no branch it holds.
        set_head = [GIT, "remote", "set-head", "origin", "-a"]
        run(set_head, cwd=repo, env=env, capture_output=True, check=False)
    return [line.split()[0] for line in _git(repo, env, "ls-remote", "origin").splitlines()]


def install_gh(sandbox: pathlib.Path, replies: tuple[Reply, ...]) -> None:
    """Put the recording `gh` stub in `sandbox/bin`, with `replies` and its log in `sandbox/gh-stub`.

    `sandbox/gh-config` is made empty, for the session's GH_CONFIG_DIR.
    """
    (sandbox / "bin").mkdir()
    (sandbox / "gh-config").mkdir()
    (sandbox / GH_STATE).mkdir()
    stub = sandbox / "bin" / "gh"
    stub.write_text("#!/usr/bin/env -S python3 -I\n" + GH_STUB.read_text())
    stub.chmod(0o755)
    replies_json = json.dumps([asdict(r) for r in replies])
    (sandbox / GH_STATE / REPLIES).write_text(replies_json)
    (sandbox / GH_STATE / "calls.jsonl").touch()


def gh_calls(sandbox: pathlib.Path) -> list[dict[str, object]]:
    """The calls the sandbox's `gh` stub recorded, in order; a line that is not JSON is skipped."""
    log = sandbox / GH_STATE / "calls.jsonl"
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


def verify(command: str, repo: pathlib.Path, env: dict[str, str]) -> int | None:
    """The exit code of a `verify` command run in `repo`, or None when it timed out; no shell runs it.

    A command that cannot start, such as one naming no executable, exits NOT_STARTED. Once
    the command exits or times out, every process it started is killed too, such as a
    server a test left running.
    """
    try:
        process = start(
            shlex.split(command), cwd=repo, env=env,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True,
        )  # fmt: skip
    except OSError:
        return NOT_STARTED
    try:
        code: int | None = process.wait(timeout=VERIFY_TIMEOUT_S)
    except subprocess.TimeoutExpired:
        code = None
    with contextlib.suppress(ProcessLookupError):  # the command left nothing running
        os.killpg(process.pid, signal.SIGKILL)
    process.wait()
    return code


def collect(case: Case, repo: pathlib.Path) -> dict[str, str]:
    """The text of every file a `file:` or `files:` check of the case reads, by its path in `repo`.

    A glob is matched against every file of the tree but `.git`'s and Python's caches. A
    file that is not UTF-8 is read with its bad bytes replaced, and one that resolves
    outside `repo`, through a link the agent made, is not read.
    """
    inside = repo.resolve()

    def read(path: str) -> str | None:
        file = repo / path
        if not file.is_file() or not file.resolve().is_relative_to(inside):
            return None
        return file.read_text(errors="replace")

    named = {p: read(p) for p in case.files()}
    found = {p: text for p, text in named.items() if text is not None}
    if not (globs := case.globs()):
        return found
    for folder, dirs, names in os.walk(repo):
        dirs[:] = sorted(d for d in dirs if d != ".git")
        for name in sorted(names):
            path = (pathlib.Path(folder) / name).relative_to(repo)
            if python_cache(path) or not any(glob_match(path.as_posix(), g) for g in globs):
                continue
            if (text := read(path.as_posix())) is not None:
                found[path.as_posix()] = text
    return found


def private_paths(case: Case, spec: Spec, sandbox: pathlib.Path) -> list[str]:
    """The paths a session must not name: the checkout, every working tree of its clone, suite, samples and arms.

    The clone's other working trees, the main one and each sibling worktree, hold the
    same suite and its answers. The arms are private but for the session's own, which
    `trace.classify` lets it read: another arm's copy of the text under test would let a
    `none` session read the skill it lacks. A remote case's session must not name the
    `gh` stub's directory in `sandbox`, nor its REPLIES file by any path: a reply's
    `match` can show what the case wants the agent to send.
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
    stub = [str(sandbox / GH_STATE), REPLIES] if case.remote else []
    return list(
        dict.fromkeys(
            [
                str(spec.checkout), *trees, str(case.path.parent.parent),
                str(spec.store / "samples"), str(cache.arms(spec.store)), *stub,
            ]
        )
    )  # fmt: skip


def loaded_arm(case: Case, arm: Arm) -> Arm:
    """`arm` as the case's session loads it: without the plugins the case's `without` names."""
    return replace(arm, plugins={n: d for n, d in arm.plugins.items() if n not in case.without})


def _session(
    case: Case, arm: Arm, index: int, spec: Spec, sample_key: str
) -> tuple[cache.Sample, str]:
    """Run one session in a fresh sandbox and collect what it left."""
    own = arm.root
    arm = loaded_arm(case, arm)
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
            dict(os.environ),
            spec.checkout,
            sandbox,
            spec.store,
            gh_stub=case.remote,
            suite_env=spec.env,
        )
        cut_short = ""
        with out.open("w") as handle:
            if case.turns:
                args = claude_args(None, arm, spec.model, spec.budget_usd, debug_log)
                timed_out, cut_short = converse(
                    args, (case.prompt, *case.turns),
                    cwd=repo, env=session_env, out=handle, timeout_s=spec.timeout_s,
                )  # fmt: skip
            else:
                try:
                    run(
                        claude_args(case.prompt, arm, spec.model, spec.budget_usd, debug_log),
                        cwd=repo, env=session_env, stdout=handle, stderr=subprocess.STDOUT,
                        timeout=spec.timeout_s, check=False,
                    )  # fmt: skip
                except subprocess.TimeoutExpired:
                    timed_out = True
        text = out.read_text()
        loaded = preloads(debug_log.read_text(errors="replace")) if debug_log.is_file() else []
        parsed = trace.parse(trace.load(out), arm.plugins, loaded)
        private = private_paths(case, spec, sandbox)
        reasons, spoiled = trace.classify(
            parsed, arm.plugins, spec.model, timed_out, private, own=own
        )
        reasons += [cut_short] if cut_short else []
        result = parsed.result or {}
        files = collect(case, repo)
        commits = new_commits(repo, env, heads)
        verified = {c: verify(c, repo, session_env) for c in case.commands()}
        sample = cache.Sample(
            key=sample_key,
            case=case.id,
            arm=arm.name,
            index=index,
            plugins=arm.plugins,
            valid=not reasons,
            reasons=reasons,
            commits=commits,
            final=str(result.get("result", "")),
            files=files,
            usage=trace.usage(parsed)
            | {
                "tool_calls": len(parsed.tool_inputs),
                "agents": [[r.agent, r.model] for r in parsed.reports],
            },
            spoiled=spoiled,
            collected=[*case.files(), *(FILES + g for g in case.globs())],
            preloads=[list(p) for p in loaded],
            gh=gh_calls(sandbox) if case.remote else None,
            verified=verified,
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


def key_of(case: Case, arm: Arm, index: int, spec: Spec) -> str:
    """The key of the sample (case, arm, index) under `spec`.

    RUNNER is in every key, REMOTE_RUNNER in a remote case's only, and a timeout other
    than TIMEOUT_S, or an `env`, in its suite's only.
    """
    runner = f"r{RUNNER}" + (f":g{REMOTE_RUNNER}" if case.remote else "")
    if spec.timeout_s != TIMEOUT_S:
        runner += f":t{spec.timeout_s:g}"
    if spec.env:
        runner += f":e{json.dumps(sorted(spec.env.items()))}"
    return cache.key(
        case.pinned(),
        f"{arm.name}:{arm.hash}:{spec.screen}:{runner}",
        spec.model,
        spec.version,
        index,
    )


def run_sample(
    case: Case, arm: Arm, index: int, spec: Spec, breaker: Breaker | None = None
) -> cache.Sample:
    """The stored sample for (case, arm, model, version, index), running the session if missing.

    An excluded sample (the infrastructure failed: a usage limit, a leaked setting, a
    session that reached the suite's files) is retried up to RETRIES times and kept
    for its reasons, never reused: the next run retries it too. When the API limits
    requests, each retry first waits, BACKOFF_S doubling, and `breaker` stops the run
    once limits persist; a sample not started then is returned as not run and not
    saved. A sample the arm spoiled is valid and counts. The arm's name is part of the
    key, so `new` never reuses `old`'s sessions even when their plugins are identical,
    and `spec.screen` is too, so each screen draws fresh samples for both arms while a
    rerun of the same screen resumes it. RUNNER is in every key, REMOTE_RUNNER in a
    remote case's only, and a timeout other than TIMEOUT_S or an `env` in its suite's
    only, so a changed timeout draws new samples instead of reusing the ones it cut off.
    """
    sample_key = key_of(case, arm, index, spec)
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
