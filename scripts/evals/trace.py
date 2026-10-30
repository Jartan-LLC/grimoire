"""Read a `claude -p --output-format stream-json --include-hook-events` trace.

Shapes, from probe runs on Claude Code 2.1.309: a `system`/`init` event lists the
loaded plugins, MCP servers and memory paths; a Skill call's tool_result says only
"Launching skill", and the skill's text follows as a synthetic user event starting
"Base directory for this skill: <path>"; a `result` event ends a turn of the main
thread, `total_cost_usd` the session's cost so far, `usage` and `num_turns` that
turn's only. The init event's `skills` list holds only user-invocable skills, so it
cannot show delivery.

Subagents, from probe runs on 2.1.311 and 2.1.314 with `--forward-subagent-text`: each
event a subagent emits carries `parent_tool_use_id`, the id of the Agent call that
started it, and its loads and writes are attributed to that agent and that call (its
spawn). A subagent's own subagents are sent too, their events naming their own Agent
call. Other events carry the field as well (a long tool call's heartbeats name the call
itself), so only a followed Agent call's id makes an event a subagent's. A foreground
Agent call's result carries the report in `tool_use_result`. Under `-p` on 2.1.314 the
main thread's Agent calls run in the background: the call's result only says the agent
was launched, and the report comes later as a `system`/`task_notification` event, its
`tool_use_id` the call's and its `summary` the report; each notification starts a new
main-thread turn, whose `result` event arrives only when the session ends. A subagent's
own Agent calls run in the foreground, and their results carry no `tool_use_result`, but
they get a notification too. The skills an agent's frontmatter preloads reach no event:
Claude Code's debug log names them, and `parse` takes them as `preloads`.
"""

import json
import pathlib
import posixpath
import re
from collections.abc import Iterator, Sequence
from dataclasses import dataclass, field
from typing import cast

SKILL_TEXT = "Base directory for this skill: "
AGENT = "Agent"
DEFAULT_AGENT = "general-purpose"  # the agent an Agent call without `subagent_type` starts
# Claude Code's note atop a report, not the agent's text.
HARNESS_NOTE = "<tools-used-before-summary>"
# git's global options may come before the subcommand: `git -c user.name="A B" commit`.
_WORD = r"""(?:[^\s"']|"[^"]*"|'[^']*')+"""
_GIT = rf"\bgit(?:\s+(?:-[cC]\s+{_WORD}|--?[\w-]+(?:={_WORD})?))*\s+"
WRITES = (
    ("commit", re.compile(_GIT + r"commit\b")),
    ("push", re.compile(_GIT + r"push\b")),
    ("pr", re.compile(r"\bgh\s+pr\s+(create|edit|review)\b")),
    ("issue", re.compile(r"\bgh\s+issue\s+(create|comment)\b")),
)
SPAWN = "spawn"  # the write kind of an Agent call, whose text is its prompt

# An absolute path in a tool call's input, so `..` in it can be resolved away.
_PATH = re.compile(r"""(?<![\w.~-])/[^\s"'`;|&<>()]+""")

type Event = dict[str, object]


@dataclass(frozen=True)
class Write:
    """A write the agent made: `index` is where its text was fixed (the tool call).

    `agent` is the subagent that made it, empty for the main thread; `spawn` is the id of
    the Agent call that started that subagent, so two spawns of one agent stay apart.
    """

    index: int
    kind: str
    ok: bool
    text: str
    agent: str = ""
    spawn: str = ""


@dataclass(frozen=True)
class Delivery:
    """A skill's text reaching the session at event `index`; `agent` and `spawn` as for a `Write`.

    A preloaded skill is placed at the Agent call that started its agent.
    """

    index: int
    skill: str
    path: str
    agent: str = ""
    spawn: str = ""


@dataclass(frozen=True)
class Report:
    """A subagent's final report, handed back at event `index` to the Agent call `spawn`.

    It arrives as the call's result, or for a call run in the background as its
    notification, which names no model: `model` is then the one the subagent's own
    messages name.
    """

    index: int
    agent: str
    model: str
    text: str
    spawn: str = ""


@dataclass(frozen=True)
class Brief:
    """The prompt of the main thread's Agent call at event `index`, which started agent type `agent`.

    A SendMessage follow-up to the agent is not one, nor an Agent call that ended in error.
    """

    index: int
    agent: str
    text: str


@dataclass(frozen=True)
class Spawn:
    """An Agent call at event `index` that started agent type `agent`, and did not end in error.

    `id` is the call's id; `by` the spawn whose agent made the call, empty for the main
    thread; `ended` the event its agent finished at, with its report or a notification
    that it failed, None when it never finished.
    """

    id: str
    index: int
    agent: str
    by: str = ""
    ended: int | None = None


@dataclass
class Trace:
    """What the runner reads from one session; `result` is the last of `results`."""

    init: Event | None = None
    result: Event | None = None
    results: list[Event] = field(default_factory=list[Event])
    writes: list[Write] = field(default_factory=list[Write])
    deliveries: list[Delivery] = field(default_factory=list[Delivery])
    reports: list[Report] = field(default_factory=list[Report])
    briefs: list[Brief] = field(default_factory=list[Brief])
    spawns: list[Spawn] = field(default_factory=list[Spawn])
    compacts: list[int] = field(default_factory=list[int])
    hook_contexts: list[tuple[int, str]] = field(default_factory=list[tuple[int, str]])
    tool_inputs: list[str] = field(default_factory=list[str])


def load(path: pathlib.Path) -> list[Event]:
    """The JSON events of a trace file; a line that is not JSON (stderr noise) is skipped."""
    return load_text(path.read_text())


def load_text(text: str) -> list[Event]:
    """The JSON events of trace text, one per line; other lines are skipped."""
    events: list[Event] = []
    for line in text.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            events.append(cast("Event", value))
    return events


def skill_of(path: str, plugin_dirs: dict[str, str]) -> str | None:
    """`plugin:skill` for a path inside a skill of one of `plugin_dirs`, else None."""
    for plugin, root in plugin_dirs.items():
        prefix = root.rstrip("/") + "/skills/"
        if path.startswith(prefix):
            name = path[len(prefix) :].split("/", 1)[0]
            return f"{plugin}:{name}" if name else None
    return None


def _content(event: Event) -> list[dict[str, object]]:
    message = event.get("message")
    content = (
        cast("dict[str, object]", message).get("content") if isinstance(message, dict) else None
    )
    return cast("list[dict[str, object]]", content) if isinstance(content, list) else []


def _hook_context(output: str) -> str:
    for line in output.splitlines():
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        specific = (
            cast("dict[str, object]", value).get("hookSpecificOutput")
            if isinstance(value, dict)
            else None
        )
        context = (
            cast("dict[str, object]", specific).get("additionalContext")
            if isinstance(specific, dict)
            else None
        )
        if isinstance(context, str):
            return context
    return ""


def _write(name: str, tool_input: dict[str, object]) -> tuple[str, str] | None:
    if name in ("Write", "Edit"):
        return "file", str(tool_input.get("file_path", ""))
    if name == AGENT:
        return SPAWN, str(tool_input.get("prompt", ""))
    command = tool_input.get("command")
    if name == "Bash" and isinstance(command, str):
        for kind, pattern in WRITES:
            if pattern.search(command):
                return kind, command
    return None


def _system(trace: Trace, index: int, event: Event) -> None:
    subtype = event.get("subtype")
    if subtype == "init" and trace.init is None:
        trace.init = event
    elif subtype == "compact_boundary":
        trace.compacts.append(index)
    elif subtype == "hook_response" and (context := _hook_context(str(event.get("output") or ""))):
        trace.hook_contexts.append((index, context))


type Call = tuple[int, str, dict[str, object], str, str]  # index, tool name, input, agent, spawn


def _report(index: int, event: Event, agent: str, spawn: str) -> Report | None:
    """The report in an Agent call's result; None when the result holds none.

    A background call's result only says the agent was launched, and a subagent's own
    call's result carries no `tool_use_result`: their reports come as notifications.
    """
    handed = event.get("tool_use_result")
    if not isinstance(handed, dict):
        return None
    result = cast("dict[str, object]", handed)
    if result.get("isAsync") is True:
        return None
    content = result.get("content")
    blocks = cast("list[dict[str, object]]", content) if isinstance(content, list) else []
    texts = [str(b.get("text", "")) for b in blocks if b.get("type") == "text"]
    text = "\n".join(t for t in texts if not t.startswith(HARNESS_NOTE))
    return Report(index, agent, str(result.get("resolvedModel", "")), text, spawn)


def _result(
    trace: Trace, index: int, block: dict[str, object], call: Call, plugin_dirs: dict[str, str]
) -> None:
    at, name, tool_input, agent, spawn = call
    ok = block.get("is_error") is not True
    if (write := _write(name, tool_input)) is not None:
        trace.writes.append(Write(at, write[0], ok, write[1], agent, spawn))
    path = tool_input.get("file_path")
    if name == "Read" and ok and isinstance(path, str) and (skill := skill_of(path, plugin_dirs)):
        trace.deliveries.append(Delivery(index, skill, path, agent, spawn))


def _skill_text(
    trace: Trace, index: int, text: str, plugin_dirs: dict[str, str], who: tuple[str, str]
) -> None:
    """Record the skill whose text `text` is, delivered to `who`: its (agent, spawn)."""
    if not text.startswith(SKILL_TEXT):
        return
    path = text[len(SKILL_TEXT) :].split("\n", 1)[0].strip()
    if skill := skill_of(path + "/", plugin_dirs):
        trace.deliveries.append(Delivery(index, skill, path, *who))


def _preload(
    trace: Trace, spawns: dict[str, list[tuple[int, str]]], preloads: Sequence[tuple[str, str]],
    plugin_dirs: dict[str, str],
) -> None:  # fmt: skip
    """Place each preloaded skill at its agent's Agent call: the k-th preload of a skill, at the k-th call.

    Every spawn of one agent preloads the same skills, so pairing them in order can
    misplace one only between spawns that are alike. A skill named without its plugin
    is the agent's own plugin's.
    """
    seen: dict[tuple[str, str], int] = {}
    for agent, name in preloads:
        count = seen.get((agent, name), 0)
        seen[(agent, name)] = count + 1
        calls = spawns.get(agent, [])
        plugin, _, skill = name.rpartition(":")
        if not plugin and ":" in agent:
            plugin = agent.partition(":")[0]
        if count < len(calls) and plugin in plugin_dirs:
            path = plugin_dirs[plugin].rstrip("/") + "/skills/" + skill
            at, spawn = calls[count]
            trace.deliveries.append(Delivery(at, f"{plugin}:{skill}", path, agent, spawn))


def _failed_calls(events: list[Event]) -> set[str]:
    """The id of every tool call whose result is an error."""
    return {
        str(block.get("tool_use_id"))
        for event in events
        if event.get("type") == "user"
        for block in _content(event)
        if block.get("type") == "tool_result" and block.get("is_error") is True
    }


def _model(event: Event) -> str:
    message = event.get("message")
    return (
        str(cast("dict[str, object]", message).get("model", ""))
        if isinstance(message, dict)
        else ""
    )


@dataclass
class _Spawns:
    """The Agent calls `parse` follows, keyed by call id, as it reads the events."""

    agents: dict[str, str] = field(default_factory=dict[str, str])  # -> the agent it started
    launched: dict[str, tuple[int, str]] = field(default_factory=dict[str, tuple[int, str]])
    reported: dict[str, int] = field(default_factory=dict[str, int])
    ended: dict[str, int] = field(default_factory=dict[str, int])  # reported, or failed
    models: dict[str, str] = field(default_factory=dict[str, str])  # the subagent's model
    by_agent: dict[str, list[tuple[int, str]]] = field(
        default_factory=dict[str, list[tuple[int, str]]]
    )  # each agent's spawns in order, for its preloads
    briefs: dict[str, Brief] = field(default_factory=dict[str, Brief])  # the main thread's only

    def launch(self, index: int, call_id: str, inputs: dict[str, object], by: str) -> None:
        """Follow the Agent call `call_id`, made at `index` by the spawn `by` (empty: the main thread)."""
        started = str(inputs.get("subagent_type") or DEFAULT_AGENT)
        self.agents[call_id] = started
        self.launched[call_id] = (index, by)
        self.by_agent.setdefault(started, []).append((index, call_id))
        if not by:
            self.briefs[call_id] = Brief(index, started, str(inputs.get("prompt", "")))

    def answered(self, trace: Trace, index: int, event: Event, call_id: str) -> None:
        """Read the report in the result of a followed Agent call that did not end in error."""
        started = self.agents.get(call_id)
        if started is not None and (report := _report(index, event, started, call_id)):
            self.report(trace, report)

    def report(self, trace: Trace, report: Report) -> None:
        """Keep the first report of a call: one that has both a result and a notification has one report."""
        if report.spawn not in self.reported:
            trace.reports.append(report)
            self.reported[report.spawn] = report.index
            self.ended.setdefault(report.spawn, report.index)

    def notified(self, trace: Trace, index: int, event: Event) -> None:
        """A followed call's notification ends its spawn; only a completed one carries a report.

        The summary of one that failed is the error, not the agent's report.
        """
        call_id = str(event.get("tool_use_id"))
        if call_id not in self.agents:
            return
        if event.get("status") == "completed":
            agent, model = self.agents[call_id], self.models.get(call_id, "")
            self.report(trace, Report(index, agent, model, str(event.get("summary", "")), call_id))
        self.ended.setdefault(call_id, index)


def _whole(trace: Trace, index: int, event: Event, spawns: _Spawns) -> None:
    """Read what an event says whichever agent sent it: system events, results, tool inputs."""
    kind = event.get("type")
    if kind == "system":
        _system(trace, index, event)
        if event.get("subtype") == "task_notification":
            spawns.notified(trace, index, event)
    elif kind == "result":
        trace.result = event
        trace.results.append(event)
    elif kind == "assistant":
        trace.tool_inputs += [
            json.dumps(b.get("input")) for b in _content(event) if b.get("type") == "tool_use"
        ]


def parse(
    events: list[Event], plugin_dirs: dict[str, str], preloads: Sequence[tuple[str, str]] = ()
) -> Trace:
    """Read init, results, writes, skill deliveries, spawns, briefs, reports, compactions and hook context from `events`.

    `preloads` are the (agent, skill) pairs Claude Code's debug log names, in its order.
    """
    trace = Trace()
    calls: dict[str, Call] = {}
    spawns = _Spawns()
    for index, event in enumerate(events):
        kind = event.get("type")
        _whole(trace, index, event, spawns)
        parent = event.get("parent_tool_use_id")
        spawn = "" if parent is None else str(parent)
        agent = spawns.agents.get(spawn) if spawn else ""
        if agent is None:
            continue
        if kind == "assistant" and spawn and (model := _model(event)):
            spawns.models[spawn] = model
        for block in _content(event):
            block_type = block.get("type")
            if kind == "assistant" and block_type == "tool_use":
                tool_input = block.get("input")
                inputs = (
                    cast("dict[str, object]", tool_input) if isinstance(tool_input, dict) else {}
                )
                call_id, name = str(block.get("id")), str(block.get("name"))
                calls[call_id] = (index, name, inputs, agent, spawn)
                if name == AGENT:
                    spawns.launch(index, call_id, inputs, spawn)
            elif kind == "user" and block_type == "tool_result":
                call_id = str(block.get("tool_use_id"))
                if (call := calls.get(call_id)) is not None:
                    _result(trace, index, block, call, plugin_dirs)
                    if block.get("is_error") is not True:
                        spawns.answered(trace, index, event, call_id)
            elif kind == "user" and block_type == "text":
                text = str(block.get("text", ""))
                _skill_text(trace, index, text, plugin_dirs, (agent, spawn))
    failed = _failed_calls(events)
    trace.briefs = [b for call_id, b in spawns.briefs.items() if call_id not in failed]
    trace.spawns = [
        Spawn(call_id, at, spawns.agents[call_id], by, spawns.ended.get(call_id))
        for call_id, (at, by) in spawns.launched.items()
        if call_id not in failed
    ]
    _preload(trace, spawns.by_agent, preloads, plugin_dirs)
    trace.writes.sort(key=lambda w: w.index)
    trace.deliveries.sort(key=lambda d: d.index)
    return trace


SPOILING_RESULTS = ("error_max_turns", "error_max_budget_usd")


def _strings(value: object) -> Iterator[str]:
    """Every string in a decoded JSON value, so a path is read as the tool got it, not escaped."""
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for item in cast("dict[str, object]", value).values():
            yield from _strings(item)
    elif isinstance(value, list):
        for item in cast("list[object]", value):
            yield from _strings(item)


def _normalised(text: str) -> str:
    """`text` with each absolute path normalised: no `.` or `..` step, no doubled slash."""
    return _PATH.sub(lambda m: posixpath.normpath(m[0]), text)


def classify(  # noqa: PLR0913 -- `own` is apart from `private`: paths under it may be read
    trace: Trace,
    plugin_dirs: dict[str, str],
    model: str,
    timed_out: bool,
    private: list[str],
    *,
    own: str,
) -> tuple[list[str], str]:
    """Why a sample must be excluded, and how the arm spoiled it; both empty for a clean sample.

    Excluded (the infrastructure failed, so the sample says nothing about the arm):
    plugins other than the arm's at the arm's paths, an MCP server, an auto-memory
    path, another model, an error result, a crash before the result, a main-thread spawn
    that never ended though the session did, or a tool call naming one of the `private`
    paths, which hold the suite and its answers and the other arms. A path under `own`, the session's own arm, does not count: the store that holds
    it is in the clone's git directory, inside the main checkout. Quotes are dropped and
    each absolute path normalised first, so `"<own>"/../../samples` names the samples.
    Spoiled (the arm's own doing, so the sample counts and fails every check): a
    timeout, or a result cut off by the turn or budget cap.
    """
    if trace.init is None:
        return (["no init event"], "") if not timed_out else ([], "timeout")
    reasons: list[str] = []
    plugins = trace.init.get("plugins")
    loaded = {
        str(p.get("name")): str(p.get("path"))
        for p in cast("list[dict[str, object]]", plugins if isinstance(plugins, list) else [])
    }
    if loaded != plugin_dirs:
        reasons.append(f"plugins {loaded} are not the arm's {plugin_dirs}")
    if trace.init.get("mcp_servers"):
        reasons.append(f"MCP servers loaded: {trace.init.get('mcp_servers')}")
    if trace.init.get("memory_paths"):
        reasons.append(f"memory loaded: {trace.init.get('memory_paths')}")
    if trace.init.get("model") != model:
        reasons.append(f"model {trace.init.get('model')!r} is not {model!r}")
    # A path counts only whole, not followed by a character that continues a file name: a
    # worktree at /tmp/grimoire is not named by the sandbox /tmp/grimoire-eval-x, nor the
    # arm none-...-praxis-review by a sibling none-...-praxis-review-pr or ...-review+x.
    whole = {p: re.compile(re.escape(p) + r"(?![\w.~+-])") for p in [*private, own] if p}
    texts = [
        _normalised(text.replace('"', "").replace("'", ""))
        for tool_input in trace.tool_inputs
        for text in _strings(json.loads(tool_input))
    ]
    outside = [whole[own].sub("", text) for text in texts] if own else texts
    bounded = {p: at for p, at in whole.items() if p in private}
    if touched := sorted({p for p, at in bounded.items() for text in outside if at.search(text)}):
        reasons.append(f"the session reached {', '.join(touched)}")
    spoiled = ""
    result = trace.result
    if timed_out:
        spoiled = "timeout"
    elif result is None:
        reasons.append("no result event")
    elif result.get("subtype") in SPOILING_RESULTS:
        spoiled = str(result.get("subtype"))
    elif result.get("is_error"):
        reasons.append(
            f"session ended in error: {result.get('subtype')}: {str(result.get('result', ''))[:120]}"
        )
    if result is not None and not spoiled:
        # With no report and no failure notice, its checks would read no report and a wave
        # open to the end: the session closed under it (`-p` stops waiting on the background
        # after 10 idle minutes unless told otherwise), not by the arm's doing.
        reasons += [
            f"the main thread's spawn {s.id} ({s.agent}) never ended: no report and no notice "
            "that it failed came by the session's end"
            for s in trace.spawns
            if not s.by and s.ended is None
        ]
    return reasons, spoiled


def state(trace: Trace, write: Write, skill: str) -> tuple[str, bool]:
    """Where `skill` stood when `write` was made, and whether a later write of its kind followed.

    in-context: delivered before the write and no compaction since. evicted: delivered
    before, then compacted away. late: first delivered after the write; the flag says
    whether a same-kind write succeeded after that delivery (an amend or a redo).
    absent: never delivered.
    """
    times = [d.index for d in trace.deliveries if d.skill == skill]
    before = [t for t in times if t < write.index]
    if before:
        last_compact = max((c for c in trace.compacts if c < write.index), default=-1)
        return ("in-context" if max(before) > last_compact else "evicted"), False
    after = [t for t in times if t > write.index]
    if after:
        redo = any(w.kind == write.kind and w.ok and w.index > min(after) for w in trace.writes)
        return "late", redo
    return "absent", False


def _count(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def usage(trace: Trace) -> dict[str, object]:
    """The session's tokens, turns and cost.

    The cost is the last result event's, which totals the session; tokens and turns are
    summed over every result event, as each counts only its own turn of the main thread.
    A token field that is not a count (a nested table, a tier name) is the last one's.
    """
    tokens: dict[str, object] = {}
    for result in trace.results:
        found = result.get("usage")
        for name, value in cast(
            "dict[str, object]", found if isinstance(found, dict) else {}
        ).items():
            before = tokens.get(name, 0)
            summed = _count(value) and _count(before)
            tokens[name] = cast("int", before) + cast("int", value) if summed else value
    turns = [cast("int", t) for r in trace.results if _count(t := r.get("num_turns"))]
    return {
        "cost_usd": (trace.result or {}).get("total_cost_usd"),
        "turns": sum(turns) if turns else None,
        "tokens": tokens,
    }
