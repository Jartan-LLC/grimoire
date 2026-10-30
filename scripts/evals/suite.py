"""Load an eval suite: its `suite.toml` and its `cases/<id>/` directories.

A case is `prompt.md`, an optional `fixture/` directory and `build.py`, a `key.toml`
holding its split, its kind, its checks and what they rely on, and `reference/`
outputs the lint grades. `tests/evals/README.md` says how to write them.
"""

import dataclasses
import fnmatch
import hashlib
import json
import pathlib
import re
import tomllib
from dataclasses import dataclass
from typing import cast

TIMEOUT_S = 1800  # a session's wall-clock limit, unless the suite's `timeout_s` sets another

SPLITS = ("dev", "screen", "confirm")
KINDS = ("target", "regression", "cost", "trigger")
TEXT_ARTIFACTS = ("commits", "final", "gh")
REPORT = "report:"
BRIEF = "brief:"
FILES = "files:"
DIRECTIONS = ("higher",)  # every check scores 1 when it holds
RULES = ("better", "no-regression")
STATES = ("in-context", "late", "evicted", "absent", "loaded", "not-loaded")
WRITE_KINDS = ("commit", "push", "pr", "issue", "file", "spawn")
# Checks on how the session's subagents worked, read from its trace like a delivery check.
SPAWN_CHECKS = ("overlap", "spawn-writes", "barrier")
# Graded from a session only, never a reference.
SESSION_ARTIFACTS = ("delivery", "verify", *SPAWN_CHECKS)
ARMS = ("none", "old")
MAX_EXIT = 255
EFFORTS = ("low", "medium", "high", "xhigh", "max")
JUDGE_MODEL = "claude-opus-5-5"
# A suite's `env` sets CLAUDE_CODE_* variables only, never the login ones `claude_env` keeps.
ENV_PREFIX = "CLAUDE_CODE_"
LOGIN_ENV = ("CLAUDE_CODE_OAUTH_TOKEN", "CLAUDE_CODE_USE_")
JUDGE_KEYS = frozenset(
    ("id", "question", "model", "effort", "panel", "held_out", "siblings", "yes_ratings", "compare")
)

type Table = dict[str, object]


class SuiteError(ValueError):
    """A suite or case file that does not hold what the runner needs."""


@dataclass(frozen=True)
class Check:
    """One graded condition on a sample, scored 0 or 1, counted toward `metric`.

    A text check names an artifact (`commits`, `final`, `file:<path>`, `files:<glob>`
    (every file the glob matches, `glob_match`, each after a `==> <path> <==` line), `gh` (the calls
    the sandbox's `gh` recorded, Claude Code's own aside), `report:<agent>` (every report
    that agent handed back) or `brief:<agent>` (every Agent-call prompt the main thread
    sent that agent type, but for a call that ended in error)) and a `present` or
    `absent` regex, or a `judge` (a suite `[[judge]]` id) and the `reference` that judge
    reads beside the artifact, with `yes_ratings` when this case's silver labels accept
    other ratings than the judge's. A delivery check names a `skill` and a `state`: with a `write` kind,
    the state the skill must be in at every such write; without one, `loaded` or
    `not-loaded` over the whole session (trigger cases). It reads the main thread's
    deliveries and writes, or with an `agent`, that subagent's. A spawn check reads the
    session's subagents: `overlap` (no file written by two spawns), `spawn-writes` with a
    `write` kind (no spawn made such a write) or `barrier` (no main-thread file write while
    a spawn it made had not reported). A `verify` check runs its `command` on the session's
    final tree and holds when it exits 0.
    """

    metric: str
    artifact: str
    present: str | None = None
    absent: str | None = None
    skill: str | None = None
    write: str | None = None
    state: str | None = None
    agent: str = ""
    judge: str | None = None
    reference: str = ""
    yes_ratings: tuple[str, ...] = ()
    command: str | None = None


@dataclass(frozen=True)
class Judge:
    """A yes/no question a model answers about one artifact, for the judged checks naming its id.

    `model` at `effort` answers each sample `panel` times, the majority deciding. The
    rest serves calibration only (tests/evals/README.md, "Judges"): the `held_out`
    cases' items are the held-out set, never tuned on, the other cases' are dev; each
    `siblings` group holds cases whose plants are of one kind, so a report of one judged
    against another's reference is a hard "no"; `yes_ratings`, when set, derives a
    silver label from the rating the labeller reads on the matched finding; `compare`
    names the metric whose checks the judge would replace, scored on the same labels.
    """

    id: str
    question: str
    model: str = JUDGE_MODEL
    effort: str = "high"
    panel: int = 3
    held_out: tuple[str, ...] = ()
    siblings: tuple[tuple[str, ...], ...] = ()
    yes_ratings: tuple[str, ...] = ()
    compare: str = ""


@dataclass(frozen=True)
class Fact:
    """Text a check relies on, and where the writer can find it: `prompt` or `fixture:<path>`."""

    text: str
    where: str


@dataclass(frozen=True)
class Plant:
    """A planted problem: `verify` fails on the fixture and passes with `fix/` laid over it."""

    id: str
    verify: str


@dataclass(frozen=True)
class Reply:
    """A scripted answer of the sandbox's `gh`, to a call whose one-line argv (`gh_stub.call_line`) `match` finds."""

    match: str
    stdout: str = ""
    exit: int = 0


@dataclass(frozen=True)
class Baseline:
    """How often one arm failed the case on one model, and under which runner revisions.

    The counts choose cases and let the planner estimate power; a verdict never uses
    them. A count drawn under an older runner, model or Claude Code is stale, and for a
    remote case one drawn under another `remote_runner` (0 when the entry has none: drawn
    before the case had a remote); for a case without a remote, one with a `remote_runner`,
    drawn while it had one.
    """

    model: str
    arm: str
    failures: int
    runs: int
    runner: int
    remote_runner: int = 0


@dataclass(frozen=True)
class Reference:
    """An output the lint grades, from a session or by hand; `passes`: every check must hold.

    `reports` and `briefs` map an agent to the text a `report:<agent>` or `brief:<agent>`
    check reads; `gh` is the text a `gh` check reads.
    """

    name: str
    passes: bool
    commits: tuple[str, ...]
    final: str
    files: dict[str, str]
    reports: dict[str, str] = dataclasses.field(default_factory=dict[str, str])
    gh: str = ""
    briefs: dict[str, str] = dataclasses.field(default_factory=dict[str, str])


@dataclass(frozen=True)
class Case:
    """One case of a suite.

    A `remote` case's session gets a local `origin` and a `gh` that records each call
    and answers from the `gh` replies, first match first. The `origin` holds every
    fixture branch when the runner makes it; a `build.py` may make its own (see
    `session.add_origin`). A case's session loads every plugin of the arm but those
    named in `without`. `turns` are the user's later messages, each sent once the turn
    before has ended.
    """

    id: str
    path: pathlib.Path
    split: str
    kind: str
    prompt: str
    checks: tuple[Check, ...]
    hints: tuple[str, ...] = ()
    facts: tuple[Fact, ...] = ()
    plants: tuple[Plant, ...] = ()
    baselines: tuple[Baseline, ...] = ()
    remote: bool = False
    gh: tuple[Reply, ...] = ()
    without: tuple[str, ...] = ()
    turns: tuple[str, ...] = ()
    # The hash when the suite was loaded; a run keys and checks its samples against it.
    loaded: str = ""

    def failure_rate(self, model: str, arm: str) -> float | None:
        """The recorded share of runs the case failed on `model` under `arm`, or None."""
        found = [b for b in self.baselines if b.model == model and b.arm == arm]
        if not found:
            return None
        return sum(b.failures for b in found) / sum(b.runs for b in found)

    references: tuple[Reference, ...] = ()

    def files(self) -> list[str]:
        """The fixture paths a check reads after the session, to collect before cleanup."""
        return sorted({c.artifact[5:] for c in self.checks if c.artifact.startswith("file:")})

    def globs(self) -> list[str]:
        """The globs a `files:` check reads after the session: every file they match is collected."""
        return sorted(
            {c.artifact.removeprefix(FILES) for c in self.checks if c.artifact.startswith(FILES)}
        )

    def commands(self) -> list[str]:
        """The `verify` commands to run on the session's final tree before cleanup."""
        return sorted({c.command for c in self.checks if c.command is not None})

    def pinned(self) -> str:
        """The hash the case had when loaded, so a run's samples all describe one version."""
        return self.loaded or self.hash()

    def hash(self) -> str:
        """What a session depends on, as on disk now: prompt, fixture, build script; of the key, a remote case's `gh` replies, `without` and `turns`.

        Those count as loaded, not as on disk now. Each is folded in only when set, so a
        case without them keeps the hash it had before they existed.
        """
        inputs = [self.path / "prompt.md", self.path / "build.py"]
        fixture = self.path / "fixture"
        files = [p for p in inputs if p.is_file()]
        files += (
            sorted(p for p in fixture.rglob("*") if p.is_file() and not python_cache(p))
            if fixture.is_dir()
            else []
        )
        digest = tree_hash(self.path, files)
        if self.remote:
            replies = json.dumps([dataclasses.asdict(r) for r in self.gh])
            digest = hashlib.sha256(f"{digest}\0{replies}".encode()).hexdigest()
        options: dict[str, list[str]] = {}
        if self.without:
            options["without"] = sorted(self.without)
        if self.turns:
            options["turns"] = list(self.turns)
        if options:
            digest = hashlib.sha256(f"{digest}\0{json.dumps(options)}".encode()).hexdigest()
        return digest


@dataclass(frozen=True)
class Metric:
    """A suite-level measure, the mean of its checks' scores.

    `direction` is "higher", the only one: every check scores 1 when it holds. A guard's
    `margin` is the harm it tolerates; a `must_hold` metric fails the change on any failing
    sample.
    """

    id: str
    direction: str
    margin: float = 0.0
    must_hold: bool = False


@dataclass(frozen=True)
class PassRule:
    """How the per-metric verdicts combine into SHIP, HURT or INCONCLUSIVE.

    `min_effect` is the gain the primary metric should be able to show; under `better`
    the planner checks the suite can see it, and the verdict does not use it.
    """

    primary: str
    rule: str
    guards: tuple[str, ...]
    min_effect: float
    min_samples: int


@dataclass(frozen=True)
class Suite:
    """A loaded suite."""

    path: pathlib.Path
    target: str
    covers: tuple[str, ...]
    models: tuple[str, ...]
    watch: tuple[str, ...]
    metrics: dict[str, Metric]
    pass_rule: PassRule
    budget_usd: float
    timeout_s: float
    clusters: dict[str, str]
    burned: tuple[str, ...]
    cases: tuple[Case, ...]
    judges: dict[str, Judge] = dataclasses.field(default_factory=dict[str, Judge])
    replaces: tuple[str, ...] = ()
    env: dict[str, str] = dataclasses.field(default_factory=dict[str, str])
    claude_code: str = ""  # the oldest Claude Code its sessions may run on; "" for any

    def removed(self) -> tuple[str, ...]:
        """What the `none` arm removes from `old`: the target, then each text it replaces."""
        return (self.target, *self.replaces)

    def split(self, name: str | None) -> list[Case]:
        """The cases of one split, or all of them."""
        return [c for c in self.cases if name is None or c.split == name]

    def unit(self, case_id: str) -> str:
        """The unit the verdict compares: the case's cluster, or the case itself."""
        return self.clusters.get(case_id, case_id)


def glob_match(path: str, pattern: str) -> bool:
    """Whether a `/`-separated relative path matches a glob: `*`, `?` and `[...]` stay within one name, `**` spans any number."""
    return _glob_match(path.split("/"), pattern.split("/"))


def _glob_match(names: list[str], parts: list[str]) -> bool:
    if not parts:
        return not names
    if parts[0] == "**":
        return any(_glob_match(names[i:], parts[1:]) for i in range(len(names) + 1))
    return (
        bool(names)
        and fnmatch.fnmatchcase(names[0], parts[0])
        and _glob_match(names[1:], parts[1:])
    )


def older(version: str, minimum: str) -> bool:
    """Whether dotted version `version` is older than `minimum`; text after the numbers is ignored."""

    def numbers(text: str) -> tuple[int, ...]:
        found = re.match(r"\d+(?:\.\d+)*", text)
        return tuple(int(n) for n in found[0].split(".")) if found else ()

    return numbers(version) < numbers(minimum)


def _env(data: Table, where: pathlib.Path) -> dict[str, str]:
    table = data.get("env", {})
    if not isinstance(table, dict) or not all(
        isinstance(v, str) for v in cast("Table", table).values()
    ):
        raise SuiteError(f'{where}: [env] must be a table of NAME = "value" strings')
    env = cast("dict[str, str]", table)
    for name in env:
        if not name.startswith(ENV_PREFIX) or name.startswith(LOGIN_ENV):
            raise SuiteError(
                f"{where}: [env] sets {name!r}: a suite sets {ENV_PREFIX}* variables only, "
                "never a login's"
            )
    return env


def python_cache(path: pathlib.Path) -> bool:
    """A file Python writes on import, which running a fixture's tests in place leaves behind."""
    return "__pycache__" in path.parts or path.suffix == ".pyc"


def tree_hash(root: pathlib.Path, files: list[pathlib.Path]) -> str:
    """A hash of each file's path relative to `root` and its bytes."""
    digest = hashlib.sha256()
    for path in sorted(files):
        digest.update(path.relative_to(root).as_posix().encode() + b"\0")
        digest.update(path.read_bytes() + b"\0")
    return digest.hexdigest()


def _toml(path: pathlib.Path) -> Table:
    try:
        return tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise SuiteError(f"{path}: {error}") from None


def _str(table: Table, key: str, where: pathlib.Path, choices: tuple[str, ...] = ()) -> str:
    value = table.get(key)
    if not isinstance(value, str) or (choices and value not in choices):
        wanted = f"one of {', '.join(choices)}" if choices else "a string"
        raise SuiteError(f"{where}: {key!r} must be {wanted}")
    return value


def _strs(table: Table, key: str, where: pathlib.Path) -> tuple[str, ...]:
    value = table.get(key, [])
    if not isinstance(value, list) or not all(
        isinstance(v, str) for v in cast("list[object]", value)
    ):
        raise SuiteError(f"{where}: {key!r} must be a list of strings")
    return tuple(cast("list[str]", value))


def _number(table: Table, key: str, where: pathlib.Path, default: float) -> float:
    value = table.get(key, default)
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise SuiteError(f"{where}: {key!r} must be a number")
    return float(value)


def _tables(table: Table, key: str, where: pathlib.Path) -> list[Table]:
    value = table.get(key, [])
    if not isinstance(value, list) or not all(
        isinstance(v, dict) for v in cast("list[object]", value)
    ):
        raise SuiteError(f"{where}: {key!r} must be an array of tables")
    return cast("list[Table]", value)


def _regex(
    pattern: object, where: pathlib.Path, wanted: str = "'present' and 'absent' must be strings"
) -> str:
    if not isinstance(pattern, str):
        raise SuiteError(f"{where}: {wanted}")
    try:
        re.compile(pattern)
    except re.error as error:
        raise SuiteError(f"{where}: bad regex {pattern!r}: {error}") from None
    return pattern


def _check(
    table: Table, where: pathlib.Path, metrics: dict[str, Metric], judges: dict[str, Judge]
) -> Check:
    metric = _str(table, "metric", where)
    if metric not in metrics:
        raise SuiteError(f"{where}: check metric {metric!r} is not a metric of the suite")
    artifact = _str(table, "artifact", where)
    if artifact in SESSION_ARTIFACTS:
        return _session_check(table, where, metric, artifact)
    if "agent" in table:
        raise SuiteError(
            f"{where}: 'agent' is for delivery checks; a text check names it as report:<agent> "
            "or brief:<agent>"
        )
    if not (
        artifact in TEXT_ARTIFACTS
        or artifact.startswith("file:")
        or any(artifact.startswith(p) and artifact != p for p in (REPORT, BRIEF, FILES))
    ):
        raise SuiteError(
            f"{where}: artifact {artifact!r} is not commits, final, gh, file:<path>, "
            "files:<glob>, report:<agent>, brief:<agent>, delivery, verify, overlap, "
            "spawn-writes or barrier"
        )
    present, absent = table.get("present"), table.get("absent")
    if sum(table.get(k) is not None for k in ("present", "absent", "judge")) != 1:
        raise SuiteError(
            f"{where}: a text check needs exactly one of 'present', 'absent' and 'judge'"
        )
    if "judge" in table:
        return _judged(table, where, metrics[metric], judges)
    if "reference" in table or "yes_ratings" in table:
        raise SuiteError(f"{where}: 'reference' and 'yes_ratings' are for a judged check")
    if present is not None:
        return Check(metric, artifact, present=_regex(present, where))
    return Check(metric, artifact, absent=_regex(absent, where))


def _session_check(table: Table, where: pathlib.Path, metric: str, artifact: str) -> Check:
    """A delivery or spawn check, graded from the session's trace."""
    if artifact in SPAWN_CHECKS:
        write = _str(table, "write", where, WRITE_KINDS) if artifact == "spawn-writes" else None
        return Check(metric, artifact, write=write)
    if artifact == "verify":
        command = _str(table, "command", where)
        if not command.strip():
            raise SuiteError(f"{where}: a verify check's 'command' is empty")
        return Check(metric, artifact, command=command)
    skill = _str(table, "skill", where)
    agent = _str(table, "agent", where) if "agent" in table else ""
    if "write" not in table:
        return Check(
            metric,
            artifact,
            skill=skill,
            state=_str(table, "state", where, ("loaded", "not-loaded")),
            agent=agent,
        )
    write = _str(table, "write", where, WRITE_KINDS)
    return Check(
        metric,
        artifact,
        skill=skill,
        write=write,
        state=_str(table, "state", where, STATES[:4]),
        agent=agent,
    )


def _judged(table: Table, where: pathlib.Path, metric: Metric, judges: dict[str, Judge]) -> Check:
    """A judged check; on a must-hold metric one judge error in a screen would read as HURT."""
    judge = _str(table, "judge", where)
    if judge not in judges:
        raise SuiteError(f"{where}: judge {judge!r} is not a [[judge]] of the suite")
    if metric.must_hold:
        raise SuiteError(
            f"{where}: must-hold metric {metric.id!r} cannot be judged: any judge error fails it"
        )
    reference = table.get("reference")
    if not isinstance(reference, str) or not reference.strip():
        raise SuiteError(f"{where}: a judged check needs a 'reference' string")
    return Check(
        metric.id,
        _str(table, "artifact", where),
        judge=judge,
        reference=reference,
        yes_ratings=_strs(table, "yes_ratings", where),
    )


def _reference(path: pathlib.Path) -> Reference:
    data = _toml(path)
    files = data.get("files", {})
    if not isinstance(files, dict) or not all(
        isinstance(v, str) for v in cast("Table", files).values()
    ):
        raise SuiteError(f"{path}: 'files' must be a table of path = text")
    final, gh = data.get("final", ""), data.get("gh", "")
    if not isinstance(final, str) or not isinstance(gh, str):
        raise SuiteError(f"{path}: 'final' and 'gh' must be strings")
    return Reference(
        name=path.stem,
        passes=path.stem.startswith("pass"),
        commits=_strs(data, "commits", path),
        final=final,
        files=cast("dict[str, str]", files),
        reports=_agent_texts(data, "reports", path),
        gh=gh,
        briefs=_agent_texts(data, "briefs", path),
    )


def _agent_texts(data: Table, key: str, path: pathlib.Path) -> dict[str, str]:
    value = data.get(key, {})
    if not isinstance(value, dict) or not all(
        isinstance(v, str) for v in cast("Table", value).values()
    ):
        raise SuiteError(f"{path}: {key!r} must be a table of agent = text")
    return cast("dict[str, str]", value)


def _replies(key: Table, where: pathlib.Path) -> tuple[Reply, ...]:
    found: list[Reply] = []
    for table in _tables(key, "gh", where):
        if set(table) - {"match", "stdout", "exit"}:
            raise SuiteError(f"{where}: a [[gh]] takes only match, stdout and exit")
        stdout, code = table.get("stdout", ""), table.get("exit", 0)
        if not isinstance(stdout, str):
            raise SuiteError(f"{where}: a [[gh]]'s 'stdout' must be a string")
        if isinstance(code, bool) or not isinstance(code, int) or not 0 <= code <= MAX_EXIT:
            raise SuiteError(f"{where}: a [[gh]]'s 'exit' must be an integer from 0 to {MAX_EXIT}")
        found.append(
            Reply(
                _regex(table.get("match"), where, "a [[gh]] needs a 'match' string"), stdout, code
            )
        )
    return tuple(found)


def _remote(key: Table, where: pathlib.Path, replies: tuple[Reply, ...]) -> bool:
    remote = key.get("remote", bool(replies))
    if not isinstance(remote, bool):
        raise SuiteError(f"{where}: 'remote' must be true or false")
    if replies and not remote:
        raise SuiteError(f"{where}: [[gh]] replies need the remote; drop 'remote = false'")
    return remote


def _baselines(key: Table, where: pathlib.Path) -> tuple[Baseline, ...]:
    found: list[Baseline] = []
    for table in _tables(key, "baseline", where):
        failures, runs, runner = table.get("failures"), table.get("runs"), table.get("runner")
        remote_runner = table.get("remote_runner", 0)
        if not all(isinstance(v, int) for v in (failures, runs, runner, remote_runner)):
            raise SuiteError(
                f"{where}: a [[baseline]]'s 'failures', 'runs', 'runner' and 'remote_runner' "
                "must be integers"
            )
        failures, runs, runner = cast("int", failures), cast("int", runs), cast("int", runner)
        if not 0 <= failures <= runs:
            raise SuiteError(f"{where}: a [[baseline]] needs 0 <= failures <= runs")
        found.append(
            Baseline(
                _str(table, "model", where),
                _str(table, "arm", where, ARMS),
                failures,
                runs,
                runner,
                cast("int", remote_runner),
            )
        )
    return tuple(found)


def _turns(key: Table, where: pathlib.Path) -> tuple[str, ...]:
    turns = _strs(key, "turns", where)
    if any(not t.strip() for t in turns):
        raise SuiteError(f"{where}: a turn in 'turns' is empty")
    return turns


def load_case(
    path: pathlib.Path, metrics: dict[str, Metric], judges: dict[str, Judge] | None = None
) -> Case:
    """Load `cases/<id>/`, checking its key against the suite's metrics and judges."""
    key_path = path / "key.toml"
    key = _toml(key_path)
    prompt = path / "prompt.md"
    if not prompt.is_file():
        raise SuiteError(f"{path}: no prompt.md")
    checks = tuple(
        _check(t, key_path, metrics, judges or {}) for t in _tables(key, "check", key_path)
    )
    if not checks:
        raise SuiteError(f"{key_path}: no [[check]]")
    named = [c.judge for c in checks if c.judge is not None]
    if len(named) != len(set(named)):
        raise SuiteError(f"{key_path}: two checks name one judge; ask it one question per case")
    facts = tuple(
        Fact(_str(t, "text", key_path), _str(t, "where", key_path))
        for t in _tables(key, "fact", key_path)
    )
    plants = tuple(
        Plant(_str(t, "id", key_path), _str(t, "verify", key_path))
        for t in _tables(key, "plant", key_path)
    )
    references = path / "reference"
    replies = _replies(key, key_path)
    case = Case(
        id=path.name,
        path=path,
        split=_str(key, "split", key_path, SPLITS),
        kind=_str(key, "kind", key_path, KINDS),
        prompt=prompt.read_text(),
        checks=checks,
        hints=_strs(key, "hints", key_path),
        facts=facts,
        plants=plants,
        baselines=_baselines(key, key_path),
        remote=_remote(key, key_path, replies),
        gh=replies,
        without=_strs(key, "without", key_path),
        turns=_turns(key, key_path),
        references=tuple(_reference(p) for p in sorted(references.glob("*.toml")))
        if references.is_dir()
        else (),
    )
    return dataclasses.replace(case, loaded=case.hash())


def _judge(table: Table, where: pathlib.Path, metrics: dict[str, Metric]) -> Judge:
    if stray := sorted(set(table) - JUDGE_KEYS):
        raise SuiteError(f"{where}: a [[judge]] takes no {', '.join(stray)}")
    panel = table.get("panel", 3)
    if isinstance(panel, bool) or not isinstance(panel, int) or panel < 1 or panel % 2 == 0:
        raise SuiteError(f"{where}: a [[judge]]'s 'panel' must be an odd number from 1")
    siblings = table.get("siblings", [])
    if not isinstance(siblings, list) or not all(
        isinstance(g, list) and all(isinstance(c, str) for c in cast("list[object]", g))
        for g in cast("list[object]", siblings)
    ):
        raise SuiteError(f"{where}: a [[judge]]'s 'siblings' must be a list of lists of cases")
    compare = table.get("compare", "")
    if compare and compare not in metrics:
        raise SuiteError(f"{where}: a [[judge]]'s 'compare' names {compare!r}, not a metric")
    judge = Judge(
        id=_str(table, "id", where),
        question=_str(table, "question", where),
        model=_str(table, "model", where) if "model" in table else JUDGE_MODEL,
        effort=_str(table, "effort", where, EFFORTS) if "effort" in table else "high",
        panel=panel,
        held_out=_strs(table, "held_out", where),
        siblings=tuple(tuple(cast("list[str]", g)) for g in cast("list[object]", siblings)),
        yes_ratings=_strs(table, "yes_ratings", where),
        compare=str(compare),
    )
    if not judge.question.strip():
        raise SuiteError(f"{where}: judge {judge.id!r} has an empty 'question'")
    return judge


def _judges(data: Table, where: pathlib.Path, metrics: dict[str, Metric]) -> dict[str, Judge]:
    judges: dict[str, Judge] = {}
    for table in _tables(data, "judge", where):
        judge = _judge(table, where, metrics)
        if judge.id in judges:
            raise SuiteError(f"{where}: two [[judge]] tables have id {judge.id!r}")
        judges[judge.id] = judge
    return judges


def _judge_cases(where: pathlib.Path, judges: dict[str, Judge], cases: tuple[Case, ...]) -> None:
    """Every case a judge's calibration names asks that judge."""
    for judge in judges.values():
        asking = {c.id for c in cases if any(k.judge == judge.id for k in c.checks)}
        named = [*judge.held_out, *(c for group in judge.siblings for c in group)]
        if stray := sorted({c for c in named if c not in asking}):
            raise SuiteError(
                f"{where}: judge {judge.id!r} names {', '.join(stray)}, "
                "which no check of theirs asks it"
            )


def _metrics(data: Table, where: pathlib.Path) -> dict[str, Metric]:
    metrics: dict[str, Metric] = {}
    for table in _tables(data, "metric", where):
        must_hold = table.get("must_hold", False)
        if not isinstance(must_hold, bool):
            raise SuiteError(f"{where}: metric 'must_hold' must be true or false")
        metric = Metric(
            _str(table, "id", where),
            _str(table, "direction", where, DIRECTIONS),
            _number(table, "margin", where, 0.0),
            must_hold,
        )
        metrics[metric.id] = metric
    return metrics


def _pass_rule(data: Table, where: pathlib.Path, metrics: dict[str, Metric]) -> PassRule:
    rule = data.get("pass_rule")
    if not isinstance(rule, dict):
        raise SuiteError(f"{where}: no [pass_rule]")
    table = cast("Table", rule)
    min_samples = table.get("min_samples", 3)
    if not isinstance(min_samples, int):
        raise SuiteError(f"{where}: pass_rule 'min_samples' must be an integer")
    pass_rule = PassRule(
        primary=_str(table, "primary", where),
        rule=_str(table, "rule", where, RULES),
        guards=_strs(table, "guards", where),
        min_effect=_number(table, "min_effect", where, 0.0),
        min_samples=min_samples,
    )
    for metric in (pass_rule.primary, *pass_rule.guards):
        if metric not in metrics:
            raise SuiteError(f"{where}: pass_rule names {metric!r}, which is not a metric")
        no_regression_primary = metric == pass_rule.primary and pass_rule.rule == "no-regression"
        if (metric in pass_rule.guards or no_regression_primary) and metrics[metric].margin <= 0:
            raise SuiteError(
                f"{where}: {metric!r} is tested for non-inferiority and needs a margin > 0"
            )
        if metrics[metric].must_hold:
            raise SuiteError(
                f"{where}: pass_rule names must-hold metric {metric!r}; it is judged on its own"
            )
    return pass_rule


def load_suite(path: pathlib.Path) -> Suite:
    """Load the suite in directory `path`."""
    where = path / "suite.toml"
    data = _toml(where)
    metrics = _metrics(data, where)
    pass_rule = _pass_rule(data, where, metrics)
    judges = _judges(data, where, metrics)
    cases_dir = path / "cases"
    cases = (
        tuple(load_case(p, metrics, judges) for p in sorted(cases_dir.iterdir()) if p.is_dir())
        if cases_dir.is_dir()
        else ()
    )
    if not cases:
        raise SuiteError(f"{path}: no cases/<id>/ directories")
    _judge_cases(where, judges, cases)
    ids = {c.id for c in cases}
    clusters: dict[str, str] = {}
    for table in _tables(data, "cluster", where):
        name = _str(table, "id", where)
        for case_id in _strs(table, "cases", where):
            if case_id not in ids:
                raise SuiteError(
                    f"{where}: cluster {name!r} names {case_id!r}, which is not a case"
                )
            if case_id in clusters:
                raise SuiteError(f"{where}: case {case_id!r} is in two clusters")
            clusters[case_id] = name
    target = _str(data, "target", where)
    models = _strs(data, "models", where) or ("claude-opus-5-5",)
    watch = _strs(data, "watch", where)
    if stray := [m for m in watch if m not in models]:
        raise SuiteError(f"{where}: watch names {stray}, which are not in models")
    replaces = _strs(data, "replaces", where)
    claude_code = _str(data, "claude_code", where) if "claude_code" in data else ""
    if claude_code and not re.fullmatch(r"\d+(\.\d+)*", claude_code):
        raise SuiteError(f"{where}: 'claude_code' must be a version such as \"2.1.302\"")
    if any(":" not in t for t in (target, *replaces)):
        raise SuiteError(f"{where}: 'target' and each of 'replaces' must be <plugin>:<name>")
    return Suite(
        path=path,
        target=target,
        covers=_strs(data, "covers", where),
        models=models,
        watch=watch,
        metrics=metrics,
        pass_rule=pass_rule,
        budget_usd=_number(data, "budget_usd", where, 2.0),
        timeout_s=_number(data, "timeout_s", where, TIMEOUT_S),
        clusters=clusters,
        burned=_strs(data, "BURNED", where),
        cases=cases,
        judges=judges,
        replaces=replaces,
        env=_env(data, where),
        claude_code=claude_code,
    )
