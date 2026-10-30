"""Events shaped as probe runs on Claude Code 2.1.309 (2.1.311 and 2.1.314 for subagents) emitted them."""

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


def test_parse_leaves_out_an_event_whose_parent_is_no_agent_call() -> None:
    event = call("c1", "Bash", command="git commit -m x") | {"parent_tool_use_id": "agent-1"}
    assert trace.parse([event, result_of("c1")], PLUGINS).writes == []


REVIEWER = "praxis:general-reviewer"


def spawn(call_id: str, agent: str | None = REVIEWER) -> trace.Event:
    return call(
        call_id, "Agent", prompt="Review it.", **({"subagent_type": agent} if agent else {})
    )


def inside(call_id: str, events: list[trace.Event]) -> list[trace.Event]:
    return [e | {"parent_tool_use_id": call_id} for e in events]


def handed_back(call_id: str, *texts: str, error: bool = False) -> trace.Event:
    content = [
        {"type": "text", "text": "<tools-used-before-summary>Bash</tools-used-before-summary>\n"}
    ]
    content += [{"type": "text", "text": t} for t in texts]
    return result_of(call_id, error=error) | {
        "tool_use_result": {"resolvedModel": "claude-sonnet-5-5", "content": content}
    }


def test_parse_attributes_a_subagents_loads_writes_and_report_to_its_agent() -> None:
    events = [
        spawn("a1"),
        *inside("a1", [*load_skill("s1", "gitwise:commit-pr-writing", CPW), *commit("c1")]),
        handed_back("a1", "[CRITICAL] mean divides by n - 1", "Verdict: BLOCK"),
        *commit("c2"),
    ]
    parsed = trace.parse(events, PLUGINS)
    assert [(w.index, w.kind, w.agent, w.spawn) for w in parsed.writes] == [
        (0, "spawn", "", ""), (4, "commit", REVIEWER, "a1"), (7, "commit", "", ""),
    ]  # fmt: skip
    assert [(d.skill, d.agent, d.spawn) for d in parsed.deliveries] == [
        ("gitwise:commit-pr-writing", REVIEWER, "a1")
    ]
    assert parsed.reports == [
        trace.Report(
            6,
            REVIEWER,
            "claude-sonnet-5-5",
            "[CRITICAL] mean divides by n - 1\nVerdict: BLOCK",
            "a1",
        )
    ]
    assert parsed.spawns == [trace.Spawn("a1", 0, REVIEWER, "", 6)]


def test_parse_names_an_agent_call_without_a_type_general_purpose_and_skips_a_failed_report() -> (
    None
):
    events = [spawn("a1", None), *inside("a1", commit("c1")), handed_back("a1", "x", error=True)]
    parsed = trace.parse(events, PLUGINS)
    assert [w.agent for w in parsed.writes if w.kind == "commit"] == ["general-purpose"]
    assert parsed.reports == []


def test_parse_keeps_each_brief_the_main_thread_sent_in_order_and_no_subagents_or_failed_calls() -> (
    None
):
    events = [
        call("a1", "Agent", prompt="Review the diff.", subagent_type=REVIEWER),
        *inside("a1", [call("n1", "Agent", prompt="Nested.", subagent_type="x")]),
        call("g1", "Agent", prompt="Find the tests."),
        call("a2", "Agent", prompt="Review again.", subagent_type=REVIEWER),
        call("a3", "Agent", prompt="No such agent.", subagent_type="praxis:missing"),
        result_of("a3", error=True),
    ]
    assert trace.parse(events, PLUGINS).briefs == [
        trace.Brief(0, REVIEWER, "Review the diff."),
        trace.Brief(2, "general-purpose", "Find the tests."),
        trace.Brief(3, REVIEWER, "Review again."),
    ]


def launched(call_id: str) -> trace.Event:
    """The result of an Agent call run in the background: no report, only the launch."""
    note = {"type": "text", "text": "Async agent launched successfully."}
    event = result_of(call_id) | {
        "tool_use_result": {"isAsync": True, "status": "async_launched", "agentId": "x"}
    }
    return event | {
        "message": {"content": [{"type": "tool_result", "tool_use_id": call_id, "content": [note]}]}
    }


def notification(call_id: str, summary: str, status: str = "completed") -> trace.Event:
    return {
        "type": "system",
        "subtype": "task_notification",
        "tool_use_id": call_id,
        "status": status,
        "summary": summary,
    }


def said(model: str) -> trace.Event:
    return {
        "type": "assistant",
        "message": {"model": model, "content": [{"type": "text", "text": "ok"}]},
    }


def test_parse_reads_a_background_agents_report_from_its_notification() -> None:
    events = [
        spawn("a1"),
        launched("a1"),
        call("b1", "Bash", command="sleep 9", run_in_background=True),
        result_of("b1"),
        *inside("a1", [said("claude-sonnet-5-5"), *commit("c1")]),
        notification("b1", "a background command's notification"),
        notification("a1", "Verdict: BLOCK"),
        RESULT,
    ]
    parsed = trace.parse(events, PLUGINS)
    assert parsed.reports == [
        trace.Report(8, REVIEWER, "claude-sonnet-5-5", "Verdict: BLOCK", "a1")
    ]
    assert parsed.spawns == [trace.Spawn("a1", 0, REVIEWER, "", 8)]
    assert [(w.agent, w.spawn) for w in parsed.writes if w.kind == "commit"] == [(REVIEWER, "a1")]


def test_parse_takes_no_report_from_a_failed_notification_but_ends_its_spawn_there() -> None:
    events = [spawn("a1"), launched("a1"), notification("a1", "API error", status="failed")]
    parsed = trace.parse(events, PLUGINS)
    assert parsed.reports == []
    assert parsed.spawns == [trace.Spawn("a1", 0, REVIEWER, "", 2)]
    assert trace.parse(events[:2], PLUGINS).spawns == [trace.Spawn("a1", 0, REVIEWER, "", None)]


def test_parse_follows_a_subagents_own_subagents_and_keeps_one_report_per_spawn() -> None:
    work = [
        *load_skill("s1", "gitwise:commit-pr-writing", CPW),
        call("w1", "Write", file_path="/repo/b.py", content="x"),
        result_of("w1"),
    ]
    events = [
        spawn("a1"),
        launched("a1"),
        *inside("a1", [call("n1", "Agent", prompt="Write b.py.", subagent_type="general-purpose")]),
        *inside("n1", work),
        notification("n1", "I wrote b.py."),
        # The nested call's result holds the report again, framed, with no tool_use_result.
        *inside("a1", [result_of("n1")]),
        notification("a1", "Done."),
    ]
    parsed = trace.parse(events, PLUGINS)
    assert [(w.kind, w.agent, w.spawn, w.text) for w in parsed.writes] == [
        ("spawn", "", "", "Review it."),
        ("spawn", REVIEWER, "a1", "Write b.py."),
        ("file", "general-purpose", "n1", "/repo/b.py"),
    ]
    assert [(d.agent, d.spawn) for d in parsed.deliveries] == [("general-purpose", "n1")]
    assert [(r.agent, r.text, r.spawn) for r in parsed.reports] == [
        ("general-purpose", "I wrote b.py.", "n1"),
        (REVIEWER, "Done.", "a1"),
    ]
    assert parsed.spawns == [
        trace.Spawn("a1", 0, REVIEWER, "", 10),
        trace.Spawn("n1", 2, "general-purpose", "a1", 8),
    ]
    assert [b.agent for b in parsed.briefs] == [REVIEWER]


def test_parse_places_each_preload_at_its_agents_call_in_order() -> None:
    events = [spawn("a1"), *commit("c1"), spawn("a2"), spawn("t1", "praxis:test-reviewer")]
    preloads = [
        (REVIEWER, "review-severity"),
        (REVIEWER, "gitwise:github-conventions"),
        (REVIEWER, "review-severity"),
        (REVIEWER, "review-severity"),  # a third preload, with only two calls to place it at
        ("praxis:test-reviewer", "other:skill"),  # a plugin the arm does not hold
    ]
    deliveries = trace.parse(events, PLUGINS, preloads).deliveries
    assert [(d.index, d.skill, d.agent) for d in deliveries] == [
        (0, "praxis:review-severity", REVIEWER),
        (0, "gitwise:github-conventions", REVIEWER),
        (3, "praxis:review-severity", REVIEWER),
    ]
    assert deliveries[0].path == "/arm/plugins/praxis/skills/review-severity"


def test_a_preload_is_in_context_at_its_agents_write() -> None:
    events = [spawn("a1"), *inside("a1", commit("c1"))]
    parsed = trace.parse(events, PLUGINS, [(REVIEWER, "review-severity")])
    assert trace.state(parsed, parsed.writes[0], "praxis:review-severity") == ("in-context", False)


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
    return trace.classify(
        trace.parse(events, PLUGINS),
        PLUGINS,
        MODEL,
        timed_out,
        ["/checkout"],
        own="/store/arms/old-1",
    )


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


def test_classify_lets_a_session_read_its_own_arm_and_no_other() -> None:
    arms = "/checkout/.git/grimoire-evals/arms"
    own = f"{arms}/none-r2-h-praxis-review"
    plugins = {"gitwise": f"{own}/plugins/gitwise"}
    skill_file = plugins["gitwise"] + "/skills/commit-pr-writing/SKILL.md"
    events = [
        init(plugins=[{"name": "gitwise", "path": plugins["gitwise"]}]),
        call("r1", "Read", file_path=skill_file),
        result_of("r1"),
        RESULT,
    ]

    def reasons(command: str | None = None) -> list[str]:
        if command is not None:
            events[1] = call("r1", "Bash", command=command)
        parsed = trace.parse(events, plugins)
        return trace.classify(parsed, plugins, MODEL, False, ["/checkout", arms], own=own)[0]

    assert reasons() == []
    assert reasons(f"ls {own}/plugins {own}") == []
    other_arm = f"the session reached /checkout, {arms}"
    assert reasons(f"cat {arms}/old-1/plugins/gitwise/skills/commit-pr-writing/SKILL.md") == [
        other_arm
    ]
    assert reasons(f"ls {own}-pr/plugins") == [other_arm]
    assert reasons(f"ls {own}+praxis-x/plugins") == [other_arm]
    assert reasons(f"ls {arms}") == [other_arm]
    assert reasons(f"cat {skill_file} /checkout/tests/evals/x/key.toml") == [
        "the session reached /checkout"
    ]


def test_classify_from_a_worktree_catches_the_main_checkout_and_a_path_back_out_of_the_arms() -> (
    None
):
    main = "/main"
    arms = f"{main}/.git/grimoire-evals/arms"
    samples = f"{main}/.git/grimoire-evals/samples"
    private = [
        f"{main}/.claude/worktrees/w",
        main,
        f"{main}/.claude/worktrees/w/tests/evals/x",
        samples,
        arms,
    ]
    plugins = {"gitwise": f"{arms}/old-1/plugins/gitwise"}

    def reasons(command: str) -> list[str]:
        events = [
            init(plugins=[{"name": "gitwise", "path": plugins["gitwise"]}]),
            call("r1", "Bash", command=command),
            result_of("r1"),
            RESULT,
        ]
        parsed = trace.parse(events, plugins)
        return trace.classify(parsed, plugins, MODEL, False, private, own=f"{arms}/old-1")[0]

    assert reasons(f"cat {plugins['gitwise']}/skills/s/SKILL.md") == []
    assert reasons(f"ls {arms}/new-2/plugins") == [f"the session reached /main, {arms}"]
    assert reasons(f"cat {main}/tests/evals/x/cases/c1/reference/pass.toml") == [
        "the session reached /main"
    ]
    assert reasons(f'ls "{arms}/../samples"') == [f"the session reached /main, {samples}"]
    assert reasons(f'ls "{arms}"/../samples') == [f"the session reached /main, {samples}"]
    assert reasons(f"ls '{arms}'/../samples") == [f"the session reached /main, {samples}"]
    assert reasons(f"ls {arms}/./old-1/../../samples/k.json.gz") == [
        f"the session reached /main, {samples}"
    ]
    assert reasons(f"true\n{arms}/../samples") == [f"the session reached /main, {samples}"]


def test_classify_catches_a_private_path_written_with_a_doubled_slash() -> None:
    command = "cat /workspaces//grimoire/key.toml"
    events = [init(), call("r1", "Bash", command=command), result_of("r1")]
    parsed = trace.parse([*events, RESULT], PLUGINS)
    private = ["/workspaces/grimoire"]
    assert trace.classify(parsed, PLUGINS, MODEL, False, private, own="/store/arms/old-1")[0] == [
        "the session reached /workspaces/grimoire"
    ]


def test_classify_matches_a_private_path_only_whole() -> None:
    def reasons(command: str, private: list[str]) -> list[str]:
        events = [init(), call("r1", "Bash", command=command), result_of("r1"), RESULT]
        parsed = trace.parse(events, PLUGINS)
        return trace.classify(parsed, PLUGINS, MODEL, False, private, own="/store/arms/old-1")[0]

    worktree, sandbox = "/t/grimoire", "/t/grimoire-eval-x"
    assert reasons(f"cat {sandbox}/repo/a.md {worktree}.bak", [worktree]) == []
    assert reasons(f"cat {worktree}/a.md", [f"{sandbox}/gh-stub"]) == []
    for named in (worktree, f"{worktree}/key.toml", f"cd {worktree};ls", f"PATH={worktree}:/bin"):
        assert reasons(named, [worktree]) == [f"the session reached {worktree}"]
    stub = f"{sandbox}/gh-stub"
    assert reasons(f"cat {stub}-x {stub}s", [stub]) == []
    assert reasons(f"ls {stub}", [stub]) == [f"the session reached {stub}"]


def test_classify_excludes_a_session_that_reached_the_gh_stubs_replies() -> None:
    private = ["/checkout", "/sandbox/gh", "gh-stub-replies.json"]

    def reasons(command: str) -> list[str]:
        events = [init(), call("r1", "Bash", command=command), result_of("r1"), RESULT]
        parsed = trace.parse(events, PLUGINS)
        return trace.classify(parsed, PLUGINS, MODEL, False, private, own="/store/arms/old-1")[0]

    assert reasons("cat ../gh-stub/gh-stub-replies.json") == [
        "the session reached gh-stub-replies.json"
    ]
    assert reasons("cat fixture/replies.json") == []
    assert reasons("ls /sandbox/gh") == ["the session reached /sandbox/gh"]
    assert reasons("gh pr create --draft --fill") == []


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


def test_usage_sums_turns_and_tokens_over_every_turn_and_takes_the_last_cost() -> None:
    first = RESULT | {"usage": {"output_tokens": 10, "service_tier": "standard"}}
    last = RESULT | {
        "total_cost_usd": 0.5,
        "num_turns": 2,
        "usage": {"output_tokens": 5, "input_tokens": 7, "service_tier": "priority"},
    }
    assert trace.usage(trace.parse([first, last], PLUGINS)) == {
        "cost_usd": 0.5,
        "turns": 5,
        "tokens": {"output_tokens": 15, "service_tier": "priority", "input_tokens": 7},
    }
    assert trace.usage(trace.parse([], PLUGINS)) == {"cost_usd": None, "turns": None, "tokens": {}}


def test_load_text_skips_lines_that_are_not_json_objects() -> None:
    assert trace.load_text('{"type": "result"}\nnot json\n[1]\n') == [{"type": "result"}]
