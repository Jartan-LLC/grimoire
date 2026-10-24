import pathlib

import pytest
from evals.suite import SuiteError, load_suite
from helpers import KEY, SUITE, write_suite


def test_load_suite_reads_metrics_rule_and_cases(tmp_path: pathlib.Path) -> None:
    suite = load_suite(write_suite(tmp_path))
    assert list(suite.metrics) == ["kept", "delivered"]
    assert suite.pass_rule.guards == ("delivered",)
    assert suite.budget_usd == 2.0
    (case,) = suite.cases
    assert (case.id, case.split, case.kind, len(case.checks)) == ("c1", "dev", "target", 3)
    assert suite.split("screen") == []


def test_case_hash_covers_prompt_and_fixture_but_not_the_key(tmp_path: pathlib.Path) -> None:
    root = write_suite(tmp_path)
    before = load_suite(root).cases[0].hash()
    (root / "cases" / "c1" / "key.toml").write_text(KEY.replace("#42", "#43"))
    assert load_suite(root).cases[0].hash() == before
    (root / "cases" / "c1" / "fixture" / "app.py").write_text("x = 2\n")
    assert load_suite(root).cases[0].hash() != before


@pytest.mark.parametrize(
    ("suite", "key", "message"),
    [
        (
            SUITE,
            KEY.replace('metric = "kept"', 'metric = "lost"', 1),
            "check metric 'lost' is not a metric",
        ),
        (
            SUITE,
            KEY.replace("present = '#42'", "present = '#42'\nabsent = 'x'"),
            "exactly one of 'present' and 'absent'",
        ),
        (SUITE, KEY.replace("present = '#42'", "present = '(['"), "bad regex"),
        (SUITE, KEY.replace('artifact = "commits"', 'artifact = "diff"'), "is not commits, final"),
        (SUITE, KEY.replace('state = "in-context"', 'state = "loaded"'), "'state' must be one of"),
        (SUITE, KEY.replace('split = "dev"', 'split = "train"'), "'split' must be one of"),
        (
            SUITE.replace('guards = ["delivered"]', 'guards = ["cost"]'),
            KEY,
            "pass_rule names 'cost'",
        ),
        (SUITE.replace("[pass_rule]", "[rule]"), KEY, "no [pass_rule]"),
        (SUITE, "split = ", "Invalid"),
    ],
)
def test_load_suite_names_the_file_and_the_problem(
    tmp_path: pathlib.Path, suite: str, key: str, message: str
) -> None:
    with pytest.raises(SuiteError, match=message.replace("[", r"\[").replace("(", r"\(")):
        load_suite(write_suite(tmp_path, suite, key))


def test_load_suite_fails_a_suite_without_cases(tmp_path: pathlib.Path) -> None:
    (tmp_path / "suite.toml").write_text(SUITE)
    with pytest.raises(SuiteError, match="no cases"):
        load_suite(tmp_path)


def test_load_suite_reads_target_facts_baseline_hints_and_references(
    tmp_path: pathlib.Path,
) -> None:
    root = write_suite(tmp_path)
    reference = root / "cases" / "c1" / "reference"
    reference.mkdir()
    (reference / "pass-1.toml").write_text(
        'commits = ["fix: y\\n\\nCloses #42"]\nfinal = "Done."\n'
    )
    (reference / "fail-1.toml").write_text('commits = ["fix: y"]\nfinal = "Done."\n')
    suite = load_suite(root)
    case = suite.cases[0]
    assert suite.target == "gitwise:commit-pr-writing"
    assert suite.models == ("claude-opus-5-5",)
    assert case.hints == ("issue number",)
    assert [(f.text, f.where) for f in case.facts] == [("42", "prompt")]
    (baseline,) = case.baselines
    assert (baseline.model, baseline.arm, baseline.failures, baseline.runs, baseline.runner) == (
        "claude-opus-5-5", "old", 2, 3, 2,
    )  # fmt: skip
    assert case.failure_rate("claude-opus-5-5", "old") == 2 / 3
    assert case.failure_rate("claude-opus-5-5", "none") is None
    assert case.failure_rate("claude-haiku-5-5", "old") is None
    assert [(r.name, r.passes) for r in case.references] == [("fail-1", False), ("pass-1", True)]


def test_clusters_map_cases_to_one_unit(tmp_path: pathlib.Path) -> None:
    suite = load_suite(
        write_suite(tmp_path, SUITE + '\n[[cluster]]\nid = "issue-ids"\ncases = ["c1"]\n')
    )
    assert suite.unit("c1") == "issue-ids"
    assert suite.unit("c9") == "c9"


@pytest.mark.parametrize(
    ("suite", "key", "message"),
    [
        (
            SUITE.replace('target = "gitwise:commit-pr-writing"\n', ""),
            KEY,
            "'target' must be a string",
        ),
        (
            SUITE.replace('target = "gitwise:commit-pr-writing"', 'target = "commit-pr-writing"'),
            KEY,
            "<plugin>:<name>",
        ),
        (
            SUITE + '\n[[cluster]]\nid = "x"\ncases = ["c2"]\n',
            KEY,
            "names 'c2', which is not a case",
        ),
        (SUITE, KEY.replace("failures = 2", "failures = 4"), "0 <= failures <= runs"),
        (SUITE, KEY.replace("runner = 2", 'runner = "2"'), "must be integers"),
        (SUITE, KEY.replace('arm = "old"', 'arm = "new"'), "'arm' must be one of"),
        ('watch = ["claude-haiku-5-5"]\n' + SUITE, KEY, "watch names"),
        (SUITE, KEY.replace('state = "in-context"', 'state = "loaded"'), "'state' must be one of"),
    ],
)
def test_load_suite_rejects_bad_new_fields(
    tmp_path: pathlib.Path, suite: str, key: str, message: str
) -> None:
    with pytest.raises(SuiteError, match=message.replace("<", r"\<").replace("(", r"\(")):
        load_suite(write_suite(tmp_path, suite, key))
