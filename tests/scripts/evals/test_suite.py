import pathlib

import pytest
from evals.suite import Reply, SuiteError, glob_match, load_suite
from helpers import JUDGE, JUDGED, KEY, SUITE, write_suite


def test_load_suite_reads_metrics_rule_and_cases(tmp_path: pathlib.Path) -> None:
    suite = load_suite(write_suite(tmp_path))
    assert list(suite.metrics) == ["kept", "delivered"]
    assert suite.pass_rule.guards == ("delivered",)
    assert suite.budget_usd == 2.0
    assert suite.timeout_s == 1800
    (case,) = suite.cases
    assert (case.id, case.split, case.kind, len(case.checks)) == ("c1", "dev", "target", 3)
    assert suite.split("screen") == []


def test_load_suite_reads_a_session_timeout(tmp_path: pathlib.Path) -> None:
    suite = load_suite(
        write_suite(tmp_path, SUITE.replace("target =", "timeout_s = 3600\ntarget =", 1))
    )
    assert suite.timeout_s == 3600


def test_case_hash_covers_prompt_and_fixture_but_not_the_key(tmp_path: pathlib.Path) -> None:
    root = write_suite(tmp_path)
    before = load_suite(root).cases[0].hash()
    (root / "cases" / "c1" / "key.toml").write_text(KEY.replace("#42", "#43"))
    assert load_suite(root).cases[0].hash() == before
    (root / "cases" / "c1" / "fixture" / "app.py").write_text("x = 2\n")
    changed = load_suite(root).cases[0].hash()
    assert changed != before
    (root / "cases" / "c1" / "build.py").write_text("print('history')\n")
    assert load_suite(root).cases[0].hash() != changed


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
            "exactly one of 'present', 'absent' and 'judge'",
        ),
        (
            SUITE + JUDGE,
            KEY + JUDGED.replace('judge = "flags"', 'judge = "other"'),
            "judge 'other' is not",
        ),
        (SUITE + JUDGE, KEY + JUDGED.replace('reference = "Issue 42."', ""), "needs a 'reference'"),
        (
            SUITE + JUDGE,
            KEY + JUDGED.replace("judge = ", "present = 'x'\njudge = "),
            "exactly one of",
        ),
        (
            SUITE + JUDGE,
            KEY.replace("present = '#42'", "present = '#42'\nreference = 'x'"),
            "'reference' and 'yes_ratings' are for",
        ),
        (
            SUITE + JUDGE,
            KEY.replace("present = '#42'", "present = '#42'\nyes_ratings = ['Minor']"),
            "'reference' and 'yes_ratings' are for",
        ),
        (SUITE + JUDGE, KEY + JUDGED + JUDGED, "two checks name one judge"),
        (
            SUITE + JUDGE.replace("question", "panel = 2\nquestion"),
            KEY + JUDGED,
            "'panel' must be an odd",
        ),
        (
            SUITE + JUDGE.replace("question", "rubric = 1\nquestion"),
            KEY + JUDGED,
            "takes no rubric",
        ),
        (
            SUITE + JUDGE.replace("question", 'effort = "huge"\nquestion'),
            KEY + JUDGED,
            "'effort' must be one",
        ),
        (
            SUITE + JUDGE.replace("question", 'compare = "lost"\nquestion'),
            KEY + JUDGED,
            "'compare' names 'lost'",
        ),
        (
            SUITE + JUDGE.replace("question", 'held_out = ["c2"]\nquestion'),
            KEY + JUDGED,
            "names c2, which no",
        ),
        (SUITE + JUDGE + JUDGE, KEY + JUDGED, "tables have id 'flags'"),
        (
            SUITE.replace(
                'id = "kept"\ndirection = "higher"',
                'id = "held"\ndirection = "higher"\nmust_hold = true\n\n[[metric]]\nid = "kept"\ndirection = "higher"',
            )
            + JUDGE,
            KEY + JUDGED.replace('metric = "kept"', 'metric = "held"'),
            "must-hold metric 'held' cannot be judged",
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
        (
            SUITE.replace(
                'id = "delivered"\ndirection = "higher"\nmargin = 0.2',
                'id = "delivered"\ndirection = "higher"',
            ),
            KEY,
            "'delivered' is tested for non-inferiority and needs a margin > 0",
        ),
        (
            SUITE.replace('id = "kept"\ndirection = "higher"', 'id = "kept"\ndirection = "lower"'),
            KEY,
            "'direction' must be one of",
        ),
        (
            SUITE.replace(
                'id = "delivered"\ndirection = "higher"',
                'id = "delivered"\ndirection = "higher"\nmust_hold = true',
            ),
            KEY,
            "must-hold metric 'delivered'",
        ),
        (SUITE, "split = ", "Invalid"),
        (
            SUITE.replace("target =", 'timeout_s = "1h"\ntarget =', 1),
            KEY,
            "'timeout_s' must be a number",
        ),
    ],
)
def test_load_suite_names_the_file_and_the_problem(
    tmp_path: pathlib.Path, suite: str, key: str, message: str
) -> None:
    with pytest.raises(SuiteError, match=message.replace("[", r"\[").replace("(", r"\(")):
        load_suite(write_suite(tmp_path, suite, key))


def test_a_judge_and_its_check_load_with_the_defaults(tmp_path: pathlib.Path) -> None:
    siblings = '[[judge]]\nheld_out = ["c1"]\nsiblings = [["c1"]]\nyes_ratings = ["Important"]\n'
    suite = load_suite(
        write_suite(tmp_path, SUITE + JUDGE.replace("[[judge]]\n", siblings), KEY + JUDGED)
    )
    judge = suite.judges["flags"]
    assert (judge.model, judge.effort, judge.panel) == ("claude-opus-5-5", "high", 3)
    assert (judge.held_out, judge.siblings, judge.yes_ratings) == (
        ("c1",),
        (("c1",),),
        ("Important",),
    )
    check = suite.cases[0].checks[-1]
    assert (check.metric, check.judge, check.reference, check.present) == (
        "kept",
        "flags",
        "Issue 42.",
        None,
    )


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
        (SUITE, KEY.replace('artifact = "commits"', 'artifact = "report:"'), "is not commits"),
        (
            SUITE,
            KEY.replace('artifact = "commits"', 'artifact = "commits"\nagent = "praxis:x"'),
            "'agent' is for delivery checks",
        ),
        (
            SUITE,
            KEY.replace('state = "in-context"', 'state = "in-context"\nagent = 3'),
            "'agent' must be a string",
        ),
    ],
)
def test_load_suite_rejects_bad_new_fields(
    tmp_path: pathlib.Path, suite: str, key: str, message: str
) -> None:
    with pytest.raises(SuiteError, match=message.replace("<", r"\<").replace("(", r"\(")):
        load_suite(write_suite(tmp_path, suite, key))


def test_a_check_can_read_an_agents_report_and_its_deliveries(tmp_path: pathlib.Path) -> None:
    key = KEY.replace(
        'artifact = "commits"', 'artifact = "report:praxis:general-reviewer"'
    ).replace('state = "in-context"', 'state = "in-context"\nagent = "praxis:general-reviewer"')
    root = write_suite(tmp_path, key=key)
    reference = root / "cases" / "c1" / "reference"
    reference.mkdir()
    (reference / "pass-1.toml").write_text('[reports]\n"praxis:general-reviewer" = "Closes #42"\n')
    (reference / "fail-1.toml").write_text("reports = 3\n")
    with pytest.raises(SuiteError, match="'reports' must be a table"):
        load_suite(root)
    (reference / "fail-1.toml").unlink()
    case = load_suite(root).cases[0]
    report, _, delivery = case.checks
    assert report.artifact == "report:praxis:general-reviewer"
    assert (delivery.agent, report.agent) == ("praxis:general-reviewer", "")
    assert case.references[0].reports == {"praxis:general-reviewer": "Closes #42"}


GH = """
[[gh]]
match = '^pr create'
stdout = "https://github.com/o/r/pull/7\\n"

[[gh]]
match = '^pr ready'
exit = 1
"""


def test_gh_replies_give_a_case_its_remote_and_count_in_its_hash(tmp_path: pathlib.Path) -> None:
    root = write_suite(tmp_path, key=KEY + GH)
    case = load_suite(root).cases[0]
    assert case.remote
    assert case.gh == (
        Reply("^pr create", "https://github.com/o/r/pull/7\n", 0),
        Reply("^pr ready", "", 1),
    )
    (root / "cases" / "c1" / "key.toml").write_text(KEY + GH.replace("exit = 1", "exit = 2"))
    assert load_suite(root).cases[0].hash() != case.hash()
    (root / "cases" / "c1" / "key.toml").write_text("remote = true\n" + KEY)
    remote_only = load_suite(root).cases[0]
    assert (remote_only.remote, remote_only.gh) == (True, ())
    (root / "cases" / "c1" / "key.toml").write_text(KEY)
    assert not load_suite(root).cases[0].remote


@pytest.mark.parametrize(
    ("key", "message"),
    [
        ('remote = "yes"\n' + KEY, "'remote' must be true or false"),
        ("remote = false\n" + KEY + GH, "drop 'remote = false'"),
        (KEY + GH.replace("match = '^pr ready'", ""), "a [[gh]] needs a 'match' string"),
        (KEY + GH.replace("'^pr ready'", "'(['"), "bad regex"),
        (KEY + GH.replace("exit = 1", "exit = true"), "'exit' must be an integer from 0 to 255"),
        (KEY + GH.replace("exit = 1", "exit = 256"), "'exit' must be an integer from 0 to 255"),
        (KEY + GH.replace('stdout = "', 'stdout = 3 #"'), "'stdout' must be a string"),
        (
            KEY + GH.replace("exit = 1", "exit_code = 1"),
            "a [[gh]] takes only match, stdout and exit",
        ),
        (KEY.replace('artifact = "commits"', 'artifact = "brief:"'), "is not commits"),
    ],
)
def test_load_suite_rejects_bad_remote_and_gh_fields(
    tmp_path: pathlib.Path, key: str, message: str
) -> None:
    with pytest.raises(SuiteError, match=message.replace("[", r"\[").replace("(", r"\(")):
        load_suite(write_suite(tmp_path, key=key))


def test_a_check_can_read_the_gh_calls_and_an_agents_briefs(tmp_path: pathlib.Path) -> None:
    key = KEY.replace('artifact = "commits"', 'artifact = "gh"')
    key = key.replace('artifact = "final"', 'artifact = "brief:praxis:general-reviewer"') + GH
    root = write_suite(tmp_path, key=key)
    reference = root / "cases" / "c1" / "reference"
    reference.mkdir()
    (reference / "pass-1.toml").write_text(
        'gh = "gh pr create --draft"\n[briefs]\n"praxis:general-reviewer" = "Review #42."\n'
    )
    case = load_suite(root).cases[0]
    assert [c.artifact for c in case.checks[:2]] == ["gh", "brief:praxis:general-reviewer"]
    (pass_1,) = case.references
    assert (pass_1.gh, pass_1.briefs) == (
        "gh pr create --draft",
        {"praxis:general-reviewer": "Review #42."},
    )
    (reference / "pass-1.toml").write_text("gh = 3\n")
    with pytest.raises(SuiteError, match="'final' and 'gh' must be strings"):
        load_suite(root)


SPAWN_CHECKS = """
[[check]]
metric = "kept"
artifact = "overlap"

[[check]]
metric = "kept"
artifact = "spawn-writes"
write = "commit"

[[check]]
metric = "kept"
artifact = "barrier"

[[check]]
metric = "delivered"
artifact = "delivery"
skill = "gitwise:commit-pr-writing"
write = "spawn"
state = "in-context"
"""


def test_spawn_checks_load(tmp_path: pathlib.Path) -> None:
    key = KEY.split("[[check]]")[0] + SPAWN_CHECKS
    case = load_suite(write_suite(tmp_path, key=key)).cases[0]
    assert [(c.artifact, c.write) for c in case.checks] == [
        ("overlap", None), ("spawn-writes", "commit"), ("barrier", None), ("delivery", "spawn"),
    ]  # fmt: skip
    with pytest.raises(SuiteError, match="'write' must be one of"):
        load_suite(write_suite(tmp_path / "x", key=key.replace('write = "commit"', "")))


def test_glob_match_keeps_a_star_within_one_name_and_lets_two_span_any() -> None:
    assert glob_match("src/a.py", "src/*.py")
    assert not glob_match("src/pkg/a.py", "src/*.py")
    assert glob_match("src/pkg/a.py", "src/**/*.py")
    assert glob_match("src/a.py", "src/**/*.py")
    assert glob_match("src/pkg/a.py", "**")
    assert glob_match(".hidden/a.py", "*/a.py")
    assert not glob_match("src", "src/**/*.py")


def test_files_and_verify_checks_load_and_name_what_the_session_collects(
    tmp_path: pathlib.Path,
) -> None:
    key = KEY + (
        '\n[[check]]\nmetric = "kept"\nartifact = "files:src/**/*.py"\npresent = "x"\n'
        '\n[[check]]\nmetric = "kept"\nartifact = "verify"\ncommand = "python3 -m pytest"\n'
    )
    case = load_suite(write_suite(tmp_path, key=key)).cases[0]
    assert (case.files(), case.globs(), case.commands()) == (
        [],
        ["src/**/*.py"],
        ["python3 -m pytest"],
    )
    for command, message in (("", "'command' must be a string"), ('command = " "', "is empty")):
        broken = key.replace('command = "python3 -m pytest"', command)
        with pytest.raises(SuiteError, match=message):
            load_suite(write_suite(tmp_path / message[:4], key=broken))
    with pytest.raises(SuiteError, match="is not commits"):
        load_suite(write_suite(tmp_path / "e", key=key.replace("files:src/**/*.py", "files:")))


def test_a_suite_names_what_its_target_replaces(tmp_path: pathlib.Path) -> None:
    replacing = SUITE.replace("target =", 'replaces = ["recursio:old-skill"]\ntarget =', 1)
    suite = load_suite(write_suite(tmp_path / "a", replacing))
    assert suite.removed() == ("gitwise:commit-pr-writing", "recursio:old-skill")
    assert load_suite(write_suite(tmp_path / "b")).removed() == ("gitwise:commit-pr-writing",)
    with pytest.raises(SuiteError, match="each of 'replaces' must be <plugin>:<name>"):
        load_suite(write_suite(tmp_path / "c", replacing.replace("recursio:old-skill", "old")))
