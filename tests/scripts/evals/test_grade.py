import pathlib
import re

import pytest
from evals import gh_stub, grade, trace
from evals.cache import Sample
from evals.suite import Case, Check, Reference, load_suite
from helpers import JUDGE, JUDGED, KEY, SUITE, write_suite
from test_trace import CPW, PLUGINS, REVIEWER, commit, handed_back, inside, load_skill, spawn


def sample(commits: list[str], final: str, spoiled: str = "") -> Sample:
    files = {"notes.md": "kept #42"}
    return Sample("k", "c1", "new", 0, PLUGINS, True, [], commits, final, files, {}, spoiled)


def test_scores_average_each_metrics_checks(tmp_path: pathlib.Path) -> None:
    case = load_suite(write_suite(tmp_path)).cases[0]
    delivered = trace.parse([*load_skill("s1", "x", CPW), *commit("c1")], PLUGINS)
    good = sample(["fix: y\n\nCloses #42"], "Done.")
    assert grade.scores(case, good, delivered) == {"kept": 1.0, "delivered": 1.0}
    late = trace.parse([*commit("c1"), *load_skill("s1", "x", CPW)], PLUGINS)
    bad = sample(["fix: y"], "Merging is all.")
    assert grade.scores(case, bad, late) == {"kept": 0.5, "delivered": 0.0}


def test_a_spoiled_sample_fails_every_check(tmp_path: pathlib.Path) -> None:
    case = load_suite(write_suite(tmp_path)).cases[0]
    delivered = trace.parse([*load_skill("s1", "x", CPW), *commit("c1")], PLUGINS)
    spoiled = sample(["fix: y\n\nCloses #42"], "Done.", spoiled="timeout")
    assert grade.scores(case, spoiled, delivered) == {"kept": 0.0, "delivered": 0.0}


def test_an_absent_check_fails_on_empty_output() -> None:
    check = Check("kept", "final", absent="merging is all")
    assert grade.text_score(check, "Done.") == 1.0
    assert grade.text_score(check, "merging is all") == 0.0
    assert grade.text_score(check, "  \n") == 0.0


def test_a_delivery_check_fails_when_nothing_of_its_kind_was_written() -> None:
    check = Check(
        "delivered",
        "delivery",
        skill="gitwise:commit-pr-writing",
        write="commit",
        state="in-context",
    )
    assert grade.delivery_score(check, trace.parse(load_skill("s1", "x", CPW), PLUGINS)) == 0.0


def test_a_trigger_check_asks_only_whether_the_skill_ever_loaded() -> None:
    loaded = Check("t", "delivery", skill="gitwise:commit-pr-writing", state="loaded")
    not_loaded = Check("t", "delivery", skill="gitwise:commit-pr-writing", state="not-loaded")
    with_skill = trace.parse(load_skill("s1", "x", CPW), PLUGINS)
    without = trace.parse(commit("c1"), PLUGINS)
    assert (grade.delivery_score(loaded, with_skill), grade.delivery_score(loaded, without)) == (
        1.0,
        0.0,
    )
    assert (
        grade.delivery_score(not_loaded, with_skill),
        grade.delivery_score(not_loaded, without),
    ) == (0.0, 1.0)


def test_text_of_reads_commits_final_and_collected_files() -> None:
    outputs = grade.Outputs(["a", "b"], "end", {"notes.md": "kept #42"})
    assert grade.text_of(outputs, "commits") == "a\n\nb"
    assert grade.text_of(outputs, "final") == "end"
    assert grade.text_of(outputs, "file:notes.md") == "kept #42"
    assert grade.text_of(outputs, "file:missing.md") == ""


def test_a_delivery_check_reads_only_its_own_agents_loads_and_writes() -> None:
    main = Check(
        "d", "delivery", skill="gitwise:commit-pr-writing", write="commit", state="in-context"
    )
    reviewer = Check(
        "d", "delivery", skill="gitwise:commit-pr-writing", write="commit", state="in-context",
        agent=REVIEWER,
    )  # fmt: skip
    loaded_inside = trace.parse(
        [spawn("a1"), *inside("a1", [*load_skill("s1", "x", CPW), *commit("c1")]), *commit("c2")],
        PLUGINS,
    )
    assert grade.delivery_score(reviewer, loaded_inside) == 1.0
    assert grade.delivery_score(main, loaded_inside) == 0.0
    loaded_outside = trace.parse(
        [*load_skill("s1", "x", CPW), spawn("a1"), *inside("a1", commit("c1"))], PLUGINS
    )
    assert grade.delivery_score(reviewer, loaded_outside) == 0.0


def test_a_report_check_reads_every_report_its_agent_handed_back() -> None:
    parsed = trace.parse(
        [spawn("a1"), handed_back("a1", "first"), spawn("a2"), handed_back("a2", "second")], PLUGINS
    )
    outputs = grade.Outputs(reports=grade.reports_of(parsed))
    assert grade.text_of(outputs, f"report:{REVIEWER}") == "first\n\nsecond"
    assert grade.text_of(outputs, "report:praxis:test-reviewer") == ""


def test_the_gh_artifact_lists_each_call_then_every_text_it_passed() -> None:
    calls: list[dict[str, object]] = [
        {"argv": ["pr", "create", "--draft", "-F", "b.md"], "stdin": "", "files": {"b.md": "Body"}},
        {"argv": ["pr", "view", "7"], "stdin": "", "files": {}},
        {"argv": ["api", "x", "-F", "body=@-"], "stdin": "Piped", "files": {}},
    ]
    gh = grade.gh_text(calls)
    lines, texts = gh.split("\n\n", 1)
    assert lines == "gh pr create --draft -F b.md\ngh pr view 7\ngh api x -F body=@-"
    assert texts.split("\n\n") == [
        *("pr", "create", "--draft", "-F", "b.md", "Body", "view", "7"),
        *("api", "x", "body=@-", "@-", "-", "Piped"),
    ]
    assert grade.gh_text([]) == ""
    assert grade.text_of(grade.Outputs(gh=gh), "gh") == gh


def test_the_gh_artifact_keeps_a_multi_line_body_off_the_call_lines() -> None:
    body = "Fixes it.\n\nCloses #42"
    argv = ["pr", "create", "--body", body, "--draft"]
    gh = grade.gh_text([{"argv": argv, "stdin": "", "files": {}}])
    lines = Check("m", "gh", r"^gh pr create.*--draft", None)
    assert grade.text_score(lines, gh) == 1.0
    assert grade.text_score(Check("m", "gh", r"^Closes #42$", None), gh) == 1.0
    assert gh.split("\n")[0] == "gh pr create --body Fixes it.\\n\\nCloses #42 --draft"


# The README's call-line forms: a flag on a subcommand, and no such call made.
DRAFT = r"\A(?:.+\n)*gh (?:.* )?pr create\b.*--draft"
NO_READY = r"\A(?!(?:.+\n)*gh (?:.* )?pr ready\b)"


def test_a_check_on_a_flag_reads_the_call_lines_only_in_the_call_line_form() -> None:
    quoting = "Open it as a draft:\ngh pr create --draft --fill\n"
    call: dict[str, object] = {"argv": ["pr", "create", "-F", "b.md"], "stdin": ""}
    gh = grade.gh_text([{**call, "files": {"b.md": quoting}}])
    caret = Check("m", "gh", r"^gh pr create .*--draft", None)
    call_lines = Check("m", "gh", DRAFT, None)
    assert grade.text_score(caret, gh) == 1.0
    assert grade.text_score(call_lines, gh) == 0.0
    view: dict[str, object] = {"argv": ["pr", "view", "7"], "stdin": "", "files": {}}
    made = grade.gh_text([view, {**view, "argv": ["pr", "create", "--draft", "--fill"]}])
    assert grade.text_score(call_lines, made) == 1.0


def test_the_call_line_forms_find_the_subcommand_after_a_gh_flag() -> None:
    def call(*argv: str, body: str = "") -> dict[str, object]:
        return {"argv": list(argv), "stdin": "", "files": {"b.md": body} if body else {}}

    draft, no_ready = Check("m", "gh", DRAFT, None), Check("m", "gh", NO_READY, None)
    made = grade.gh_text([call("-R", "o/r", "pr", "create", "--draft", "--fill")])
    assert grade.text_score(draft, made) == 1.0
    assert grade.text_score(no_ready, made) == 1.0
    readied = grade.gh_text([call("pr", "view", "7"), call("-R", "a/b", "pr", "ready", "7")])
    assert grade.text_score(no_ready, readied) == 0.0
    quoting = "Then:\ngh -R o/r pr create --draft\ngh -R a/b pr ready 7\n"
    quoted = grade.gh_text([call("-R", "o/r", "pr", "create", "-F", "b.md", body=quoting)])
    assert grade.text_score(draft, quoted) == 0.0
    assert grade.text_score(no_ready, quoted) == 1.0
    assert grade.text_score(no_ready, grade.gh_text([])) == 1.0


BODY = "Fixes the quoting.\nCloses #42"
# Each way gh takes a body: inline, from a file `f`, or from stdin.
FORMS = [
    ["--body", BODY], [f"--body={BODY}"], [f"-b{BODY}"], ["-b", BODY],
    ["-f", f"body={BODY}"], [f"-fbody={BODY}"],
    ["-F", "body=@f"], ["-Fbody=@f"], ["--field=body=@f"],
    ["--body-file", "f"], ["--body-file=f"], ["-Ff"], ["--input", "f"],
    ["--notes", BODY], ["-n", BODY], ["--comment", BODY], ["-c", BODY],
    ["--body-file", "-"], ["--input", "@-"], ["-F", "k=@-"],
]  # fmt: skip
# Flags that take no value in these commands: none may swallow the form after it.
BOOLEANS = [
    ["pr", "create"], ["pr", "create", "-f"], ["pr", "create", "--fill"],
    ["pr", "create", "--draft"], ["pr", "review", "7", "--comment"], ["pr", "review", "7", "-c"],
]  # fmt: skip


@pytest.mark.parametrize("before", BOOLEANS, ids=" ".join)
@pytest.mark.parametrize("form", FORMS, ids=" ".join)
def test_the_gh_artifact_holds_each_line_of_a_body_however_it_was_passed(
    tmp_path: pathlib.Path, before: list[str], form: list[str]
) -> None:
    (tmp_path / "f").write_text(BODY)
    piped = "-" in (c for arg in form for c in gh_stub.candidates(arg))

    def stdin() -> str:
        assert piped, "stdin read for a call that names no `-`"
        return BODY

    entry = gh_stub.record([*before, *form], stdin, tmp_path, (tmp_path,))
    gh = grade.gh_text([entry])
    for line in BODY.split("\n"):
        assert grade.text_score(Check("m", "gh", f"^{re.escape(line)}$", None), gh) == 1.0


def test_a_brief_check_reads_every_prompt_the_main_thread_sent_its_agent() -> None:
    parsed = trace.parse(
        [
            spawn("a1"),
            *inside("a1", [spawn("n1")]),
            spawn("a2"),
            spawn("t1", "praxis:test-reviewer"),
        ],
        PLUGINS,
    )
    outputs = grade.Outputs(briefs=grade.briefs_of(parsed))
    assert grade.text_of(outputs, f"brief:{REVIEWER}") == "Review it.\n\nReview it."
    assert grade.text_of(outputs, "brief:praxis:test-reviewer") == "Review it."
    assert grade.text_of(outputs, "brief:praxis:other") == ""


def test_scores_grade_a_gh_check_on_the_samples_recorded_calls(tmp_path: pathlib.Path) -> None:
    key = "remote = true\n" + KEY.replace('artifact = "commits"', 'artifact = "gh"')
    case = load_suite(write_suite(tmp_path, key=key)).cases[0]
    parsed = trace.parse([*load_skill("s1", "x", CPW), *commit("c1")], PLUGINS)
    drawn = sample([], "Done.")
    drawn.gh = [{"argv": ["pr", "create", "--body", "Closes #42"], "stdin": "", "files": {}}]
    assert grade.scores(case, drawn, parsed)["kept"] == 1.0
    drawn.gh = []
    assert grade.scores(case, drawn, parsed)["kept"] == 0.5


def test_an_absent_gh_check_fails_when_only_claude_code_called_gh(tmp_path: pathlib.Path) -> None:
    key = "remote = true\n" + KEY.replace(
        "artifact = \"commits\"\npresent = '#42'", "artifact = \"gh\"\nabsent = '--draft'"
    )
    case = load_suite(write_suite(tmp_path, key=key)).cases[0]
    parsed = trace.parse([*load_skill("s1", "x", CPW), *commit("c1")], PLUGINS)
    drawn = sample([], "Done.")
    own: list[dict[str, object]] = [
        {"argv": ["pr", "view", "--json", "url"], "stdin": "", "files": {}},
        {"argv": ["pr", "view", "fix/quotes", "--json", "url"], "stdin": "", "files": {}},
    ]
    drawn.gh = own
    assert grade.scores(case, drawn, parsed)["kept"] == 0.5
    drawn.gh = [*own, {"argv": ["pr", "create", "--body", "Closes #42"], "stdin": "", "files": {}}]
    assert grade.scores(case, drawn, parsed)["kept"] == 1.0


def test_a_present_or_absent_gh_check_reads_none_of_claude_codes_own_calls() -> None:
    own: list[dict[str, object]] = [
        {"argv": ["pr", "view", "--json", "url"], "stdin": "", "files": {}}
    ]
    agent: list[dict[str, object]] = [
        *own,
        {"argv": ["pr", "create", "--body", "Closes #42"], "stdin": "", "files": {}},
    ]
    present = Check("m", "gh", r"^gh pr view", None)
    assert grade.check_score(present, grade.Outputs(gh=grade.gh_text(own))) == 0.0
    absent = Check("m", "gh", None, r"--json url")
    assert grade.check_score(absent, grade.Outputs(gh=grade.gh_text(agent))) == 1.0


@pytest.mark.parametrize(
    "line",
    ["gh pr view 7 --json url", "gh pr view --json url,title", "gh pr view -R o/r b --json url"],
)
def test_a_call_that_only_resembles_claude_codes_own_counts_as_the_agents(line: str) -> None:
    assert grade.agents_gh(line) == line


def test_agents_gh_keeps_a_crlf_body_inside_its_calls_line() -> None:
    call: dict[str, object] = {"argv": ["pr", "create", "--body", "Fix\r\nCloses #42"]}
    text = grade.gh_text([{**call, "stdin": "", "files": {}}])
    assert grade.agents_gh(text) == text
    present = Check("m", "gh", r"^gh pr create .*Closes #42$", None)
    assert grade.check_score(present, grade.Outputs(gh=text)) == 1.0


def test_agents_gh_drops_claude_codes_call_lines_but_not_a_body_quoting_one() -> None:
    body = "Run\ngh pr view --json url\nto see it."
    text = f"gh pr view --json url\ngh pr create --body-file b.md\n\n{body}"
    assert grade.agents_gh(text) == f"gh pr create --body-file b.md\n\n{body}"
    assert grade.agents_gh("gh pr view --json url") == ""


def test_case_failed_counts_the_cases_own_metrics_not_the_guards() -> None:
    guards = ("format", "delivered")
    assert grade.case_failed({"rule": 0.0, "format": 1.0}, guards)
    assert not grade.case_failed({"rule": 1.0, "noted": 1.0, "delivered": 0.0}, guards)
    assert grade.case_failed({"kept": 1.0, "no_exploit": 0.5}, guards)


def test_a_file_check_the_sample_did_not_collect_refuses_to_grade(tmp_path: pathlib.Path) -> None:
    key = KEY + '\n[[check]]\nmetric = "kept"\nartifact = "file:pr-draft.md"\npresent = "fix"\n'
    case = load_suite(write_suite(tmp_path, key=key)).cases[0]
    parsed = trace.parse([*load_skill("s1", "x", CPW), *commit("c1")], PLUGINS)
    drawn_before = sample(["fix: y\n\nCloses #42"], "Done.")
    drawn_before.collected = []
    with pytest.raises(grade.Uncollected, match=r"pr-draft\.md"):
        grade.scores(case, drawn_before, parsed)
    drawn_before.collected = ["pr-draft.md"]
    assert grade.scores(case, drawn_before, parsed)["kept"] < 1


def judged_case(tmp_path: pathlib.Path) -> Case:
    return load_suite(write_suite(tmp_path, SUITE + JUDGE, KEY + JUDGED)).cases[0]


def test_a_judged_check_reads_its_panel_and_averages_with_the_regex_checks(
    tmp_path: pathlib.Path,
) -> None:
    case = judged_case(tmp_path)
    parsed = trace.parse([*load_skill("s1", "x", CPW), *commit("c1")], PLUGINS)
    good = sample(["fix: y\n\nCloses #42"], "Done.")
    assert grade.scores(case, good, parsed, {3: 1.0}) == {"kept": 1.0, "delivered": 1.0}
    assert grade.scores(case, good, parsed, {3: 0.0})["kept"] == pytest.approx(2 / 3)
    with pytest.raises(grade.Unjudged, match="check 3"):
        grade.scores(case, good, parsed)


def test_an_unjudged_check_leaves_its_whole_metric_out_when_allowed(tmp_path: pathlib.Path) -> None:
    case = judged_case(tmp_path)
    parsed = trace.parse([*load_skill("s1", "x", CPW), *commit("c1")], PLUGINS)
    good = sample(["fix: y\n\nCloses #42"], "Done.")
    # kept's two regex checks pass, but kept is not scored on them alone
    assert grade.scores(case, good, parsed, unjudged_ok=True) == {"delivered": 1.0}
    held = grade.scores(case, good, parsed, advisory={"flags"}, unjudged_ok=True)
    assert held == {"kept": 1.0, "delivered": 1.0}


def test_a_spoiled_sample_or_an_empty_artifact_fails_a_judged_check_without_a_judge(
    tmp_path: pathlib.Path,
) -> None:
    case = judged_case(tmp_path)
    parsed = trace.parse(commit("c1"), PLUGINS)
    spoiled = sample(["fix: y\n\nCloses #42"], "Done.", spoiled="timeout")
    assert grade.scores(case, spoiled, parsed)["kept"] == 0.0
    empty = sample([], "Done.")  # no commit: the regex on commits fails too, the absent check holds
    assert grade.scores(case, empty, parsed)["kept"] == pytest.approx(1 / 3)
    check = case.checks[3]
    assert grade.judged_text(check, empty, grade.outputs_of(empty, parsed)) is None
    assert grade.judged_text(check, spoiled, grade.outputs_of(spoiled, parsed)) is None


def test_a_judge_that_may_not_gate_scores_a_reported_metric_of_its_own(
    tmp_path: pathlib.Path,
) -> None:
    case = judged_case(tmp_path)
    parsed = trace.parse([*load_skill("s1", "x", CPW), *commit("c1")], PLUGINS)
    good = sample(["fix: y\n\nCloses #42"], "Done.")
    scores = grade.scores(case, good, parsed, {3: 0.0}, advisory={"flags"})
    assert scores == {"kept": 1.0, "delivered": 1.0, "kept@flags": 0.0}
    assert grade.advisory_metric(case.checks[3]) == "kept@flags"


def test_reference_scores_leave_judged_checks_out(tmp_path: pathlib.Path) -> None:
    case = judged_case(tmp_path)
    reference = Reference("pass-1", True, ("fix: y\n\nCloses #42",), "Done.", {})
    assert [c.judge for c, _ in grade.reference_scores(case, reference)] == [None, None]
