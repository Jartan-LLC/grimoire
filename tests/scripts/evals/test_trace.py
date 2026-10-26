"""Events shaped as probe runs on Claude Code 2.1.309 emitted them."""

from evals import trace

PLUGINS = {"gitwise": "/arm/plugins/gitwise", "praxis": "/arm/plugins/praxis"}
MODEL = "claude-opus-5-5"


def init(**overrides: object) -> trace.Event:
    event: trace.Event = {
        "type": "system",
        "subtype": "init",
        "model": MODEL,
        "plugins": [{"name": n, "path": p, "source": f"{n}@inline"} for n, p in PLUGINS.items()],
        "mcp_servers": [],
        "memory_paths": None,
    }
    return event | overrides


def call(call_id: str, name: str, **tool_input: object) -> trace.Event:
    return {
        "type": "assistant",
        "parent_tool_use_id": None,
        "message": {
            "content": [{"type": "tool_use", "id": call_id, "name": name, "input": tool_input}]
        },
    }


def result_of(call_id: str, *, error: bool = False) -> trace.Event:
    return {
        "type": "user",
        "parent_tool_use_id": None,
        "message": {
            "content": [{"type": "tool_result", "tool_use_id": call_id, "is_error": error}]
        },
    }


def skill_text(path: str) -> trace.Event:
    text = f"Base directory for this skill: {path}\n\n# Skill"
    return {
        "type": "user",
        "isSynthetic": True,
        "message": {"content": [{"type": "text", "text": text}]},
    }


def load_skill(call_id: str, skill: str, path: str) -> list[trace.Event]:
    return [call(call_id, "Skill", skill=skill), result_of(call_id), skill_text(path)]


def commit(call_id: str, message: str = "feat: x") -> list[trace.Event]:
    return [call(call_id, "Bash", command=f'git commit -m "{message}"'), result_of(call_id)]


RESULT: trace.Event = {
    "type": "result",
    "subtype": "success",
    "is_error": False,
    "total_cost_usd": 0.2,
    "num_turns": 3,
    "usage": {"output_tokens": 10},
}
CPW = "/arm/plugins/gitwise/skills/commit-pr-writing"
COMPACT: trace.Event = {"type": "system", "subtype": "compact_boundary"}


def test_parse_records_a_skill_delivery_from_the_synthetic_skill_text() -> None:
    parsed = trace.parse([init(), *load_skill("s1", "gitwise:commit-pr-writing", CPW)], PLUGINS)
    assert [(d.skill, d.path) for d in parsed.deliveries] == [("gitwise:commit-pr-writing", CPW)]


def test_parse_ignores_a_skill_from_outside_the_arm() -> None:
    parsed = trace.parse(
        load_skill("s1", "gitwise:commit-pr-writing", "/other/gitwise/skills/commit-pr-writing"),
        PLUGINS,
    )
    assert parsed.deliveries == []


def test_parse_counts_a_successful_read_under_a_skill_and_not_a_failed_one() -> None:
    events = [
        call("r1", "Read", file_path=f"{CPW}/SKILL.md"), result_of("r1"),
        call("r2", "Read", file_path="/arm/plugins/praxis/skills/plain-writing/SKILL.md"), result_of("r2", error=True),
    ]  # fmt: skip
    assert [d.skill for d in trace.parse(events, PLUGINS).deliveries] == [
        "gitwise:commit-pr-writing"
    ]


def test_parse_classifies_writes_by_command_and_tool() -> None:
    events = [
        *commit("c1"),
        call("p1", "Bash", command="git push origin x"), result_of("p1"),
        call("g1", "Bash", command="gh pr create --title t --body-file b.md"), result_of("g1"),
        call("i1", "Bash", command="gh issue comment 3 --body-file b.md"), result_of("i1", error=True),
        call("w1", "Write", file_path="/repo/notes.md", content="x"), result_of("w1"),
        call("l1", "Bash", command="git log --oneline"), result_of("l1"),
        call("c2", "Bash", command='git -c user.name="A B" -c user.email=a@b commit -F -'),
        result_of("c2"),
        call("c3", "Bash", command="git -C . --no-pager push"), result_of("c3"),
        call("c4", "Bash", command="git -C . log --grep commit"), result_of("c4"),
    ]  # fmt: skip
    writes = trace.parse(events, PLUGINS).writes
    assert [(w.kind, w.ok) for w in writes] == [
        ("commit", True), ("push", True), ("pr", True), ("issue", False), ("file", True),
        ("commit", True), ("push", True),
    ]  # fmt: skip


def test_parse_leaves_out_a_subagents_events() -> None:
    event = call("c1", "Bash", command="git commit -m x") | {"parent_tool_use_id": "agent-1"}
    assert trace.parse([event, result_of("c1")], PLUGINS).writes == []


def test_parse_reads_hook_context_and_compactions() -> None:
    hook: trace.Event = {
        "type": "system",
        "subtype": "hook_response",
        "output": '{"hookSpecificOutput":{"hookEventName":"PreToolUse","additionalContext":"Load it."}}',
    }
    parsed = trace.parse([hook, COMPACT], PLUGINS)
    assert parsed.hook_contexts == [(0, "Load it.")]
    assert parsed.compacts == [1]


def classify(events: list[trace.Event], timed_out: bool = False) -> tuple[list[str], str]:
    return trace.classify(trace.parse(events, PLUGINS), PLUGINS, MODEL, timed_out, ["/checkout"])


def test_classify_passes_a_clean_session() -> None:
    assert classify([init(), RESULT]) == ([], "")


def test_classify_excludes_every_leak_and_a_crash() -> None:
    event = init(
        plugins=[
            {"name": "gitwise", "path": "/arm/plugins/gitwise"},
            {"name": "cc-plugin-telemetry", "path": "builtin"},
        ],
        mcp_servers=[{"name": "claude.ai Spotify", "status": "pending"}],
        memory_paths={"auto": "/home/u/.claude/projects/x/memory/"},
        model="claude-sonnet-5-5",
    )
    reasons, spoiled = classify([event])
    assert spoiled == ""
    assert [r.split(" ")[0] for r in reasons] == ["plugins", "MCP", "memory", "model", "no"]


def test_classify_excludes_a_session_that_reached_the_suite() -> None:
    events = [
        init(),
        call("r1", "Read", file_path="/checkout/tests/evals/x/key.toml"),
        result_of("r1"),
        RESULT,
    ]
    assert classify(events) == (["the session reached /checkout"], "")


def test_classify_excludes_an_error_result_and_marks_caps_and_timeouts_as_spoiled() -> None:
    limit = RESULT | {
        "is_error": True,
        "subtype": "error_during_execution",
        "result": "usage limit",
    }
    assert classify([init(), limit])[0] == [
        "session ended in error: error_during_execution: usage limit"
    ]
    for subtype in ("error_max_budget_usd", "error_max_turns"):
        assert classify([init(), RESULT | {"is_error": True, "subtype": subtype}]) == ([], subtype)
    assert classify([init()], timed_out=True) == ([], "timeout")
    assert classify([], timed_out=True) == ([], "timeout")


def test_state_is_in_context_when_the_skill_arrived_before_the_write() -> None:
    parsed = trace.parse([*load_skill("s1", "x", CPW), *commit("c1")], PLUGINS)
    assert trace.state(parsed, parsed.writes[0], "gitwise:commit-pr-writing") == (
        "in-context",
        False,
    )


def test_state_is_late_and_records_a_redo_after_the_delivery() -> None:
    events = [*commit("c1"), *load_skill("s1", "x", CPW), *commit("c2", "fix: y")]
    parsed = trace.parse(events, PLUGINS)
    assert trace.state(parsed, parsed.writes[0], "gitwise:commit-pr-writing") == ("late", True)
    late_only = trace.parse([*commit("c1"), *load_skill("s1", "x", CPW)], PLUGINS)
    assert trace.state(late_only, late_only.writes[0], "gitwise:commit-pr-writing") == (
        "late",
        False,
    )


def test_state_is_evicted_when_a_compaction_follows_the_delivery() -> None:
    events = [
        *load_skill("s1", "x", CPW),
        COMPACT,
        *commit("c1"),
    ]
    parsed = trace.parse(events, PLUGINS)
    assert trace.state(parsed, parsed.writes[0], "gitwise:commit-pr-writing") == ("evicted", False)


def test_state_is_absent_when_the_skill_never_arrived() -> None:
    parsed = trace.parse(commit("c1"), PLUGINS)
    assert trace.state(parsed, parsed.writes[0], "gitwise:commit-pr-writing") == ("absent", False)


def test_usage_reads_the_sessions_tokens_and_cost() -> None:
    assert trace.usage(trace.parse([RESULT], PLUGINS)) == {
        "cost_usd": 0.2, "turns": 3, "tokens": {"output_tokens": 10},
    }  # fmt: skip


def test_load_text_skips_lines_that_are_not_json_objects() -> None:
    assert trace.load_text('{"type": "result"}\nnot json\n[1]\n') == [{"type": "result"}]
