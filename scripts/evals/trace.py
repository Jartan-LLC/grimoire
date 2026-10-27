"""Read a `claude -p --output-format stream-json --include-hook-events` trace.

Shapes, from probe runs on Claude Code 2.1.309: a `system`/`init` event lists the
loaded plugins, MCP servers and memory paths; a Skill call's tool_result says only
"Launching skill", and the skill's text follows as a synthetic user event starting
"Base directory for this skill: <path>"; a `result` event ends the session, its
`usage` the session's tokens and `total_cost_usd` its cost. The init event's
`skills` list holds only user-invocable skills, so it cannot show delivery.

Subagents, from probe runs on 2.1.311 with `--forward-subagent-text`: each event a
subagent emits carries `parent_tool_use_id`, the id of the main thread's Agent call
that started it, and its loads and writes are attributed to that agent. Other events
carry the field too (a long tool call's heartbeats name the call itself), so only an
Agent call's id makes an event a subagent's. The Agent call's result carries the
report in `tool_use_result`. A subagent's own subagents are not sent. The skills an
agent's frontmatter preloads reach no event: Claude Code's debug log names them, and
`parse` takes them as `preloads`.
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

# `gh` run as a command, by name or by path: first in a line or after a shell separator,
# past any assignment, option or word that runs the next one; not `gh-pages`, nor a
# word in a message.
_RUNNER_WORD = r"(?:if|then|else|do|while|until|time|command|exec|env|sudo|nohup|xargs)"
GH_RUN = re.compile(
    rf"(?:^|[;&|(`{{!])\s*(?:{_RUNNER_WORD}\s+|-\S*\s+|\w+=\S*\s+)*(?:[\w.~/-]*/)?gh(?![\w./-])",
    re.MULTILINE,
)

# An absolute path in a tool call's input, so `..` in it can be resolved away.
_PATH = re.compile(r"""(?<![\w.~-])/[^\s"'`;|&<>()]+""")

type Event = dict[str, object]


@dataclass(frozen=True)
class Write:
    """A write the agent made: `index` is where its text was fixed (the tool call).

    `agent` is the subagent that made it; empty for the main thread.
    """

    index: int
    kind: str
    ok: bool
    text: str
    agent: str = ""


@dataclass(frozen=True)
class Delivery:
    """A skill's text reaching the session at event `index`; `agent` as for a `Write`.

    A preloaded skill is placed at the Agent call that started its agent.
    """

    index: int
    skill: str
    path: str
    agent: str = ""


@dataclass(frozen=True)
class Report:
    """A subagent's final report, handed back as its Agent call's result at event `index`."""

    index: int
    agent: str
    model: str
    text: str


@dataclass(frozen=True)
class Brief:
    """The prompt of the main thread's Agent call at event `index`, which started agent type `agent`.

    A SendMessage follow-up to the agent is not one, nor an Agent call that ended in error.
    """

    index: int
    agent: str
    text: str


@dataclass
class Trace:
    """What the runner reads from one session."""

    init: Event | None = None
    result: Event | None = None
    writes: list[Write] = field(default_factory=list[Write])
    deliveries: list[Delivery] = field(default_factory=list[Delivery])
    reports: list[Report] = field(default_factory=list[Report])
    briefs: list[Brief] = field(default_factory=list[Brief])
    compacts: list[int] = field(default_factory=list[int])
    hook_contexts: list[tuple[int, str]] = field(default_factory=list[tuple[int, str]])
    tool_inputs: list[str] = field(default_factory=list[str])
    commands: list[str] = field(default_factory=list[str])  # every Bash call's, any agent's


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


type Call = tuple[int, str, dict[str, object], str]  # index, tool name, input, agent


def _report(index: int, event: Event, agent: str) -> Report:
    handed = event.get("tool_use_result")
    result = cast("dict[str, object]", handed) if isinstance(handed, dict) else {}
    content = result.get("content")
    blocks = cast("list[dict[str, object]]", content) if isinstance(content, list) else []
    texts = [str(b.get("text", "")) for b in blocks if b.get("type") == "text"]
    text = "\n".join(t for t in texts if not t.startswith(HARNESS_NOTE))
    return Report(index, agent, str(result.get("resolvedModel", "")), text)


def _result(
    trace: Trace, index: int, block: dict[str, object], call: Call, plugin_dirs: dict[str, str]
) -> None:
    at, name, tool_input, agent = call
    ok = block.get("is_error") is not True
    if (write := _write(name, tool_input)) is not None:
        trace.writes.append(Write(at, write[0], ok, write[1], agent))
    path = tool_input.get("file_path")
    if name == "Read" and ok and isinstance(path, str) and (skill := skill_of(path, plugin_dirs)):
        trace.deliveries.append(Delivery(index, skill, path, agent))


def _skill_text(
    trace: Trace, index: int, text: str, plugin_dirs: dict[str, str], agent: str
) -> None:
    if not text.startswith(SKILL_TEXT):
        return
    path = text[len(SKILL_TEXT) :].split("\n", 1)[0].strip()
    if skill := skill_of(path + "/", plugin_dirs):
        trace.deliveries.append(Delivery(index, skill, path, agent))


def _preload(
    trace: Trace, spawns: dict[str, list[int]], preloads: Sequence[tuple[str, str]],
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
            trace.deliveries.append(Delivery(calls[count], f"{plugin}:{skill}", path, agent))


def _failed_calls(events: list[Event]) -> set[str]:
    """The id of every tool call whose result is an error."""
    return {
        str(block.get("tool_use_id"))
        for event in events
        if event.get("type") == "user"
        for block in _content(event)
        if block.get("type") == "tool_result" and block.get("is_error") is True
    }


def _tool_inputs(trace: Trace, event: Event) -> None:
    """Record each tool call's input in `event`, any agent's, and each Bash call's command."""
    for block in _content(event):
        if block.get("type") != "tool_use":
            continue
        tool_input = block.get("input")
        trace.tool_inputs.append(json.dumps(tool_input))
        inputs = cast("dict[str, object]", tool_input) if isinstance(tool_input, dict) else {}
        command = inputs.get("command")
        if block.get("name") == "Bash" and isinstance(command, str):
            trace.commands.append(command)


def parse(
    events: list[Event], plugin_dirs: dict[str, str], preloads: Sequence[tuple[str, str]] = ()
) -> Trace:
    """Read init, result, writes, skill deliveries, briefs, reports, compactions and hook context from `events`.

    `preloads` are the (agent, skill) pairs Claude Code's debug log names, in its order.
    """
    trace = Trace()
    calls: dict[str, Call] = {}
    agents: dict[str, str] = {}  # each main-thread Agent call's id -> the agent it started
    spawns: dict[str, list[int]] = {}
    briefs: dict[str, Brief] = {}  # each main-thread Agent call's id -> its brief
    for index, event in enumerate(events):
        kind = event.get("type")
        if kind == "system":
            _system(trace, index, event)
        elif kind == "result":
            trace.result = event
        if kind == "assistant":
            _tool_inputs(trace, event)
        parent = event.get("parent_tool_use_id")
        agent = "" if parent is None else agents.get(str(parent))
        if agent is None:
            continue
        for block in _content(event):
            block_type = block.get("type")
            if kind == "assistant" and block_type == "tool_use":
                tool_input = block.get("input")
                inputs = (
                    cast("dict[str, object]", tool_input) if isinstance(tool_input, dict) else {}
                )
                call_id, name = str(block.get("id")), str(block.get("name"))
                calls[call_id] = (index, name, inputs, agent)
                if name == AGENT and not agent:
                    started = str(inputs.get("subagent_type") or DEFAULT_AGENT)
                    agents[call_id] = started
                    spawns.setdefault(started, []).append(index)
                    briefs[call_id] = Brief(index, started, str(inputs.get("prompt", "")))
            elif kind == "user" and block_type == "tool_result":
                if (call := calls.get(str(block.get("tool_use_id")))) is not None:
                    _result(trace, index, block, call, plugin_dirs)
                    started = agents.get(str(block.get("tool_use_id")))
                    if started is not None and block.get("is_error") is not True:
                        trace.reports.append(_report(index, event, started))
            elif kind == "user" and block_type == "text":
                _skill_text(trace, index, str(block.get("text", "")), plugin_dirs, agent)
    failed = _failed_calls(events)
    trace.briefs = [brief for call_id, brief in briefs.items() if call_id not in failed]
    _preload(trace, spawns, preloads, plugin_dirs)
    trace.writes.sort(key=lambda w: w.index)
    trace.deliveries.sort(key=lambda d: d.index)
    return trace


def runs_gh(trace: Trace) -> bool:
    """Whether a Bash call of the main thread or a subagent runs `gh`, by name or by path."""
    return any(GH_RUN.search(command) for command in trace.commands)


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
    """`text` with each absolute path holding a `.` or `..` step written without it."""
    return _PATH.sub(lambda m: posixpath.normpath(m[0]) if "/." in m[0] else m[0], text)


def classify(  # noqa: PLR0913 -- `arms` is apart from `private`: paths under it may be read
    trace: Trace,
    plugin_dirs: dict[str, str],
    model: str,
    timed_out: bool,
    private: list[str],
    *,
    arms: str,
) -> tuple[list[str], str]:
    """Why a sample must be excluded, and how the arm spoiled it; both empty for a clean sample.

    Excluded (the infrastructure failed, so the sample says nothing about the arm):
    plugins other than the arm's at the arm's paths, an MCP server, an auto-memory
    path, another model, an error result, a crash before the result, or a tool call
    naming one of the `private` paths, which hold the suite and its answers. A path under
    `arms`, the directory holding every arm, does not count: the store that holds it is
    in the clone's git directory, inside the main checkout. Quotes are dropped and a
    path's `..` steps resolved first, so `"<arms>"/../samples` names the samples.
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
    outside = [
        _normalised(text.replace('"', "").replace("'", "")).replace(arms, "")
        for tool_input in trace.tool_inputs
        for text in _strings(json.loads(tool_input))
    ]
    if touched := sorted({p for p in private for text in outside if p in text}):
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


def usage(trace: Trace) -> dict[str, object]:
    """The session's tokens and cost, from the result event."""
    result = trace.result or {}
    tokens = result.get("usage")
    return {
        "cost_usd": result.get("total_cost_usd"),
        "turns": result.get("num_turns"),
        "tokens": cast("dict[str, object]", tokens) if isinstance(tokens, dict) else {},
    }
