import json
import pathlib
from collections.abc import Callable, Sequence

import pytest
from evals import jury, labeller
from evals.labeller import Finding, Labelled
from evals.suite import Case, Judge, load_suite
from helpers import JUDGE, JUDGED, KEY, SUITE, write_suite

TEXT = "**Important**\n\n1. `stats.py`: `_median` reimplements statistics.median.\n\n**Minor**\n\n1. A name."
FOUND = (
    Finding("`stats.py`: `_median` reimplements", "**Important**", "reinvented median"),
    Finding("A name.", "Minor", "naming"),
)
PAYLOAD = {
    "findings": [{"quote": "q", "rating": "Important", "subject": "s"}],
    "match": 0,
    "answer": "yes",
    "rationale": "r",
}


def test_labelled_of_reads_a_well_formed_output() -> None:
    assert labeller.labelled_of(PAYLOAD) == Labelled(
        (Finding("q", "Important", "s"),), 0, "yes", "r"
    )


@pytest.mark.parametrize(
    "broken",
    [
        PAYLOAD | {"match": True},
        PAYLOAD | {"match": "0"},
        PAYLOAD | {"answer": "probably"},
        PAYLOAD | {"findings": "none"},
        PAYLOAD | {"findings": [{"quote": "q", "rating": "Important"}]},
        PAYLOAD | {"findings": ["q"]},
        PAYLOAD | {"rationale": None},
        "yes",
    ],
)
def test_a_malformed_output_gives_no_label(broken: object) -> None:
    assert labeller.labelled_of(broken) is None


def test_parse_wants_the_named_model_and_no_error() -> None:
    usage: dict[str, object] = {"claude-opus-5-5": {}}
    good = json.dumps({"modelUsage": usage, "structured_output": PAYLOAD})
    assert labeller.parse(good, "claude-opus-5-5") is not None
    assert labeller.parse(good, "claude-fable-5-1") is None
    assert labeller.parse("{", "claude-opus-5-5") is None
    errored = json.dumps({"modelUsage": usage, "is_error": True, "structured_output": PAYLOAD})
    assert labeller.parse(errored, "claude-opus-5-5") is None


@pytest.mark.parametrize(
    ("match", "answer", "ratings", "label"),
    [
        (0, "yes", ("Critical", "Important"), "yes"),
        (0, "no", ("Critical", "Important"), "yes"),  # the rule, not the answer, decides
        (1, "yes", ("Critical", "Important"), "no"),  # matched at Minor
        (-1, "yes", ("Critical", "Important"), "no"),
        (5, "yes", ("Critical", "Important"), "no"),  # out of range reads as no match
        (0, "unsure", ("Critical", "Important"), "unsure"),
        (0, "yes", (), "yes"),
        (-1, "yes", (), "unsure"),  # a yes with nothing matched
        (-1, "no", (), "no"),
    ],
)
def test_label_of_follows_the_matched_finding(
    match: int, answer: str, ratings: tuple[str, ...], label: str
) -> None:
    assert labeller.label_of(Labelled(FOUND, match, answer, ""), TEXT, ratings) == label


def test_a_rating_counts_by_its_first_word() -> None:
    for rating, label in (
        ("[IMPORTANT, debt]", "yes"),
        ("Important (was Critical)", "yes"),
        ("Minor, not Important", "no"),
    ):
        found = (Finding("`_median` reimplements", rating, "s"),)
        assert (
            labeller.label_of(Labelled(found, 0, "yes", ""), TEXT, ("Critical", "Important"))
            == label
        )


def test_a_matched_finding_the_text_does_not_hold_is_unsure() -> None:
    made_up = (Finding("hand-rolled median", "Important", "s"),)
    assert labeller.label_of(Labelled(made_up, 0, "yes", ""), TEXT, ("Important",)) == "unsure"
    empty = (Finding("  ", "Important", "s"),)
    assert labeller.label_of(Labelled(empty, 0, "yes", ""), TEXT, ()) == "unsure"


@pytest.mark.parametrize(
    ("votes", "label"),
    [
        (("yes", "yes", "yes"), "yes"),
        (("no", "no", "no"), "no"),
        (("yes", "yes", "no"), None),
        (("yes", "yes", "unsure"), None),
        (("unsure", "unsure", "unsure"), None),
        ((), None),
    ],
)
def test_only_a_unanimous_yes_or_no_skips_the_adjudicator(
    votes: tuple[str, ...], label: str | None
) -> None:
    assert labeller.unanimous(votes) == label


def test_the_call_key_changes_with_each_input() -> None:
    panel = labeller.Labeller("claude-opus-5-5", "xhigh")
    judge = Judge("flags", "Q?")
    base = labeller.key(panel, "case", judge, ("ref", "text"), index=0, others=())
    variants = [
        labeller.key(
            labeller.Labeller("claude-fable-5-1", "xhigh"),
            "case",
            judge,
            ("ref", "text"),
            index=0,
            others=(),
        ),
        labeller.key(
            labeller.Labeller("claude-opus-5-5", "max"),
            "case",
            judge,
            ("ref", "text"),
            index=0,
            others=(),
        ),
        labeller.key(panel, "case2", judge, ("ref", "text"), index=0, others=()),
        labeller.key(panel, "case", Judge("flags", "Q2?"), ("ref", "text"), index=0, others=()),
        labeller.key(panel, "case", judge, ("ref2", "text"), index=0, others=()),
        labeller.key(panel, "case", judge, ("ref", "text2"), index=0, others=()),
        labeller.key(panel, "case", judge, ("ref", "text"), index=1, others=()),
        labeller.key(panel, "case", judge, ("ref", "text"), index=0, others=("o",)),
    ]
    assert len({base, *variants}) == len(variants) + 1
    # the label rule is applied to the kept output, so it calls nothing again
    rule = Judge("flags", "Q?", panel=1, yes_ratings=("Important",))
    assert labeller.key(panel, "case", rule, ("ref", "text"), index=0, others=()) == base


@pytest.mark.parametrize(
    ("name", "value"), [("SYSTEM", "Label it."), ("ADJUDICATE", "Decide."), ("SCHEMA", {})]
)
def test_the_call_key_changes_with_each_prompt_text(
    name: str, value: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    panel, judge = labeller.Labeller("claude-opus-5-5", "xhigh"), Judge("flags", "Q?")
    base = labeller.key(panel, "case", judge, ("ref", "text"), index=0, others=())
    monkeypatch.setattr(labeller, name, value)
    assert labeller.key(panel, "case", judge, ("ref", "text"), index=0, others=()) != base


def test_only_the_adjudicator_sees_the_labellers_work() -> None:
    plain = labeller.prompt("Review it.", "diff", "Q?", "ref", "report")
    assert "<labeller>" not in plain
    assert "(no diff" in labeller.prompt("Review it.", "", "Q?", "ref", "report")
    judged = labeller.prompt(
        "Review it.", "diff", "Q?", "ref", "report", others=("one", "two", "three")
    )
    assert judged.count("<labeller>") == 3
    assert judged.startswith(plain.rstrip("\n"))


def test_a_cases_own_ratings_override_the_judges(tmp_path: pathlib.Path) -> None:
    judge = '\n[[judge]]\nid = "flags"\nquestion = "Q?"\nyes_ratings = ["Critical", "Important"]\n'
    plain = load_suite(write_suite(tmp_path / "plain", SUITE + judge, KEY + JUDGED))
    assert labeller.ratings(plain.cases[0], plain.judges["flags"]) == ("Critical", "Important")
    strict = JUDGED + 'yes_ratings = ["Critical"]\n'
    own = load_suite(write_suite(tmp_path / "own", SUITE + judge, KEY + strict))
    assert labeller.ratings(own.cases[0], own.judges["flags"]) == ("Critical",)
    important = Labelled((Finding("`_median` reimplements", "Important", "s"),), 0, "yes", "")
    assert (
        labeller.label_of(important, TEXT, labeller.ratings(own.cases[0], own.judges["flags"]))
        == "no"
    )


def test_args_give_the_labeller_read_only_tools() -> None:
    line = labeller.args("claude-opus-5-5", "xhigh", "message")
    assert line[line.index("--tools") + 1] == "Read,Grep,Glob"
    assert "--restricted" in line
    assert "--dangerously-skip-permissions" not in line


def output(answer: str, quote: str = "Closes #42") -> dict[str, object]:
    """A labeller's structured output matching one finding that quotes `quote`."""
    found = [{"quote": quote, "rating": "", "subject": "the issue"}]
    return {"findings": found, "match": 0, "answer": answer, "rationale": "Read it."}


class Panel:
    """A stand-in for `labeller.call` that answers in turn and records every message."""

    def __init__(self, answers: Sequence[str | None]) -> None:
        self.answers = iter(answers)
        self.messages: list[str] = []

    def __call__(
        self, case: object, panel: object, message: Callable[[str], str]
    ) -> tuple[Labelled | None, str]:
        self.messages.append(message("the diff"))
        answer = next(self.answers)
        if answer is None:
            return None, "Error: overloaded"
        payload = output(answer)
        return labeller.labelled_of(payload), json.dumps({"structured_output": payload})


PANEL = labeller.Labeller("claude-opus-5-5", "xhigh")
ITEM = ("Issue 42.", "fix: Closes #42")


def judged_case(tmp_path: pathlib.Path) -> tuple[Case, Judge]:
    suite = load_suite(write_suite(tmp_path / "suite", SUITE + JUDGE, KEY + JUDGED))
    return suite.cases[0], suite.judges["flags"]


def test_a_unanimous_panel_takes_three_calls_and_no_adjudicator(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case, judge = judged_case(tmp_path)
    calls = Panel(["yes", "yes", "yes"])
    monkeypatch.setattr(labeller, "call", calls)
    store = tmp_path / "store"
    assert labeller.panel_label(store, PANEL, case, judge, ITEM) == (("yes",) * 3, "yes")
    assert len(calls.messages) == labeller.LABELLERS
    assert all("<labeller>" not in m for m in calls.messages)
    # kept: read back without calling
    assert labeller.panel_label(store, PANEL, case, judge, ITEM, may_call=False) == (
        ("yes",) * 3,
        "yes",
    )


def test_a_split_panel_goes_to_an_adjudicator_given_the_three_outputs(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case, judge = judged_case(tmp_path)
    calls = Panel(["yes", "no", "yes", "no"])
    monkeypatch.setattr(labeller, "call", calls)
    store = tmp_path / "store"
    assert labeller.panel_label(store, PANEL, case, judge, ITEM) == (("yes", "no", "yes"), "no")
    assert len(calls.messages) == labeller.LABELLERS + 1
    adjudicator = calls.messages[-1]
    assert adjudicator.count("<labeller>") == labeller.LABELLERS
    for answer in ("yes", "no", "yes"):
        kept = json.dumps(
            {
                "findings": [{"quote": "Closes #42", "rating": "", "subject": "the issue"}],
                "match": 0,
                "answer": answer,
                "rationale": "Read it.",
            }
        )
        assert kept in adjudicator
    assert labeller.panel_label(store, PANEL, case, judge, ITEM, may_call=False) == (
        ("yes", "no", "yes"),
        "no",
    )


@pytest.mark.parametrize("answers", [["yes", None, "yes"], ["yes", "no", "yes", None]])
def test_a_panel_missing_a_member_or_its_adjudicator_gives_no_label(
    answers: list[str | None], tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case, judge = judged_case(tmp_path)
    monkeypatch.setattr(labeller, "call", Panel(answers))
    assert labeller.panel_label(tmp_path / "store", PANEL, case, judge, ITEM) is None


def test_gold_counts_an_unsure_kept_label_as_wrong_and_a_missing_one_nowhere(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    root = write_suite(tmp_path / "suite", SUITE + JUDGE, KEY + JUDGED)
    (root / "cases" / "c1" / "reference").mkdir()
    commits = {"pass-1": "fix: Closes #42", "fail-1": "fix: Closes #42 later", "pass-2": "fix: #42"}
    for name, commit in commits.items():
        (root / "cases" / "c1" / "reference" / f"{name}.toml").write_text(
            f'commits = ["{commit}"]\nfinal = "Done."\n'
        )
    suite = load_suite(root)
    judge, case = suite.judges["flags"], suite.cases[0]
    store = tmp_path / "store"
    monkeypatch.setattr(labeller, "call", Panel(["unsure"] * 2 * (labeller.LABELLERS + 1)))
    for text in (commits["pass-1"], commits["fail-1"]):  # a yes and a no, each labelled unsure
        assert labeller.panel_label(store, PANEL, case, judge, ("Issue 42.", text))
    gold = labeller.gold_panel(suite, judge, PANEL, store, jury.Names((), ()), may_call=False)
    labelled = ("reference:c1:fail-1", "reference:c1:pass-1")
    assert gold == labeller.Gold(0, 2, labelled, ("reference:c1:pass-2",))
