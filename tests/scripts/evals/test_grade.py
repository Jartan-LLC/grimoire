import pathlib

import pytest
from evals import grade, trace
from evals.cache import Sample
from evals.suite import Check, load_suite
from helpers import KEY, write_suite
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


def test_the_gh_artifact_lists_each_call_then_the_bodies_it_sent() -> None:
    calls: list[dict[str, object]] = [
        {"argv": ["pr", "create", "--draft", "-F", "b.md"], "stdin": "", "files": {"b.md": "Body"}},
        {"argv": ["pr", "view", "7"], "stdin": "", "files": {}},
        {"argv": ["api", "x", "-F", "body=@-"], "stdin": "Piped", "files": {}},
    ]
    gh = grade.gh_text(calls)
    assert gh == (
        "gh pr create --draft -F b.md\ngh pr view 7\ngh api x -F body=@-\n\nBody\n\nPiped"
    )
    assert grade.gh_text([]) == ""
    assert grade.text_of(grade.Outputs(gh=gh), "gh") == gh


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
