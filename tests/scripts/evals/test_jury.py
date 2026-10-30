import dataclasses
import json
import pathlib

import pytest
from evals import jury
from evals.suite import Judge

JUDGE = Judge("flags", "Does the report flag the planted problem at Important?")
NAMES = jury.Names(("praxis", "gitwise"), ("comment-hygiene", "general-reviewer", "testing"))


def envelope(payload: object, model: str = "claude-opus-5-5", **extra: object) -> str:
    usage = {model: {"costUSD": 0.01}}
    return json.dumps(
        {"type": "result", "is_error": False, "modelUsage": usage}
        | extra
        | {"structured_output": payload}
    )


def test_strip_neutralises_paths_and_names_and_keeps_the_finding() -> None:
    text = (
        "**Important** `/tmp/grimoire-eval-x1y2/repo/tally/stats.py:8` reimplements "
        "statistics.median (praxis:comment-hygiene, per the general-reviewer rules of praxis). "
        "See /tmp/grimoire-eval-x1y2/venv/bin/python and "
        "/w/.git/grimoire-evals/arms/0a1b2c/plugins/praxis/x.md. Add testing."
    )
    stripped = jury.strip(text, NAMES)
    assert "`<repo>/tally/stats.py:8` reimplements statistics.median" in stripped
    assert "(<item>, per the <item> rules of <plugin>)" in stripped
    assert "<sandbox>/venv/bin/python" in stripped
    assert "<store>/plugins/<plugin>/x.md" in stripped
    assert "0a1b2c" not in stripped
    assert stripped.endswith("Add testing.")


@pytest.mark.parametrize(
    ("payload", "expected"),
    [
        ({"answer": "yes", "quote": "q"}, jury.Answer("yes", "q")),
        ({"answer": "no", "quote": ""}, jury.Answer("no", "")),
        ({"answer": "unknown", "quote": ""}, jury.Answer("unknown", "")),
        ({"answer": "maybe", "quote": ""}, None),
        ({"answer": "yes"}, None),
        ({"answer": "yes", "quote": 3}, None),
        ("yes", None),
        (None, None),
    ],
)
def test_parse_reads_a_well_formed_answer_and_nothing_else(
    payload: object, expected: jury.Answer | None
) -> None:
    assert jury.parse(envelope(payload), "claude-opus-5-5") == expected


def test_parse_refuses_malformed_json_an_error_and_another_model() -> None:
    good = {"answer": "yes", "quote": "q"}
    assert jury.parse("not json {", "claude-opus-5-5") is None
    assert jury.parse("[1]", "claude-opus-5-5") is None
    assert jury.parse(envelope(good, is_error=True), "claude-opus-5-5") is None
    assert jury.parse(envelope(good, model="claude-sonnet-5-5"), "claude-opus-5-5") is None


def test_parse_falls_back_to_a_json_result_but_never_to_prose() -> None:
    usage: dict[str, object] = {"claude-opus-5-5": {}}
    as_result = json.dumps({"modelUsage": usage, "result": '{"answer": "no", "quote": ""}'})
    prose = json.dumps({"modelUsage": usage, "result": "The answer is yes."})
    assert jury.parse(as_result, "claude-opus-5-5") == jury.Answer("no", "")
    assert jury.parse(prose, "claude-opus-5-5") is None


def test_a_yes_counts_only_with_its_quote_in_the_text() -> None:
    text = "1. **Important**: `_median`\n   reimplements statistics.median."
    assert jury.vote(jury.Answer("yes", "`_median` reimplements  statistics.median"), text) == "yes"
    assert jury.vote(jury.Answer("yes", "hand-rolled median"), text) == "unknown"
    assert jury.vote(jury.Answer("yes", "  "), text) == "unknown"
    assert jury.vote(jury.Answer("no", "anything"), text) == "no"


@pytest.mark.parametrize(
    ("votes", "score", "split"),
    [
        (("yes", "yes", "no"), 1.0, True),
        (("yes", "unknown", "no"), 0.0, True),
        (("yes", "unknown", "unknown"), 0.0, True),
        (("no", "unknown", "no"), 0.0, False),
        (("yes", "yes", "yes"), 1.0, False),
        (("yes",), 1.0, False),
    ],
)
def test_majority_counts_unknown_as_no_and_records_a_split(
    votes: tuple[str, ...], score: float, split: bool
) -> None:
    panel = jury.majority(votes)
    assert (panel.score, panel.split, panel.votes) == (score, split, votes)


def test_the_judgment_key_changes_with_each_input_and_nothing_else() -> None:
    base = jury.judgment_key(JUDGE, "ref", "text", 0)
    assert jury.judgment_key(JUDGE, "ref", "text", 0) == base
    changed = [
        jury.judgment_key(dataclasses.replace(JUDGE, model="claude-fable-5-1"), "ref", "text", 0),
        jury.judgment_key(dataclasses.replace(JUDGE, effort="max"), "ref", "text", 0),
        jury.judgment_key(dataclasses.replace(JUDGE, question="Another?"), "ref", "text", 0),
        jury.judgment_key(JUDGE, "ref2", "text", 0),
        jury.judgment_key(JUDGE, "ref", "text2", 0),
        jury.judgment_key(JUDGE, "ref", "text", 1),
    ]
    assert len({base, *changed}) == len(changed) + 1
    # Calibration-only fields and the panel size leave every call's key alone.
    other = dataclasses.replace(JUDGE, panel=5, held_out=("c1",), compare="found_regex")
    assert jury.judgment_key(other, "ref", "text", 0) == base


@pytest.mark.parametrize(
    ("name", "value"),
    [("SYSTEM", "Grade it."), ("TEMPLATE", "{question} {reference} {output}"), ("SCHEMA", {})],
)
def test_the_judgment_key_and_instrument_change_with_each_prompt_text(
    name: str, value: object, monkeypatch: pytest.MonkeyPatch
) -> None:
    key, version = jury.judgment_key(JUDGE, "ref", "text", 0), jury.instrument(JUDGE)
    monkeypatch.setattr(jury, name, value)
    assert jury.judgment_key(JUDGE, "ref", "text", 0) != key
    assert jury.instrument(JUDGE) != version


def test_the_instrument_changes_with_the_panel_and_the_call_but_not_calibration_fields() -> None:
    base = jury.instrument(JUDGE)
    assert jury.instrument(dataclasses.replace(JUDGE, panel=1)) != base
    assert jury.instrument(dataclasses.replace(JUDGE, model="claude-fable-5-1")) != base
    assert jury.instrument(dataclasses.replace(JUDGE, held_out=("c1",))) == base


def test_lookup_needs_every_panel_member(tmp_path: pathlib.Path) -> None:
    text = "**Important**: _median reimplements statistics.median"
    keys = [jury.judgment_key(JUDGE, "ref", text, i) for i in range(3)]
    jury.save(tmp_path, keys[0], jury.Answer("yes", "_median reimplements"), {})
    jury.save(tmp_path, keys[1], jury.Answer("yes", "made up"), {})
    assert jury.lookup(tmp_path, JUDGE, "ref", text) is None
    jury.save(tmp_path, keys[2], jury.Answer("no", ""), {})
    panel = jury.lookup(tmp_path, JUDGE, "ref", text)
    assert panel == jury.Panel(0.0, True, ("yes", "unknown", "no"))


def test_fill_calls_only_missing_members_and_keeps_no_failed_call(tmp_path: pathlib.Path) -> None:
    calls: list[str] = []
    answers = iter([None, "yes", "yes", "yes"])

    def calling(judge: Judge, reference: str, text: str) -> tuple[jury.Answer | None, str]:
        calls.append(text)
        said = next(answers)
        if said is None:
            return None, "Error: overloaded, try later"
        return jury.Answer(said, "a"), envelope({"answer": said, "quote": "a"})

    jury.save(tmp_path, jury.judgment_key(JUDGE, "ref", "a", 0), jury.Answer("no", ""), {})
    failed = jury.fill(tmp_path, [(JUDGE, "ref", "a")], 1, calling)
    assert len(calls) == 2
    assert len(failed) == 1
    assert "overloaded" in failed[0]
    assert jury.lookup(tmp_path, JUDGE, "ref", "a") is None
    assert jury.fill(tmp_path, [(JUDGE, "ref", "a")], 1, calling) == []
    assert len(calls) == 3
    panel = jury.lookup(tmp_path, JUDGE, "ref", "a")
    assert panel is not None
    assert panel.votes.count("yes") == 2


def test_fill_stops_calling_once_the_api_keeps_limiting(tmp_path: pathlib.Path) -> None:
    calls: list[str] = []

    def limited(judge: Judge, reference: str, text: str) -> tuple[jury.Answer | None, str]:
        calls.append(text)
        return None, "API Error: usage limit reached"

    jobs = [(JUDGE, "ref", f"text {i}") for i in range(4)]
    failed = jury.fill(tmp_path, jobs, 1, limited)
    assert len(calls) == jury.BREAKER
    assert len(failed) == 4 * JUDGE.panel
    assert sum("not called" in line for line in failed) == 4 * JUDGE.panel - jury.BREAKER


def test_an_answer_resets_the_count_of_limited_calls(tmp_path: pathlib.Path) -> None:
    said = iter([None, None, "no"])
    calls: list[str] = []

    def calling(judge: Judge, reference: str, text: str) -> tuple[jury.Answer | None, str]:
        calls.append(text)
        if next(said, None) == "no":
            return jury.Answer("no", ""), envelope({"answer": "no", "quote": ""})
        return None, "API Error: usage limit reached"

    jobs = [(JUDGE, "ref", f"text {i}") for i in range(4)]
    jury.fill(tmp_path, jobs, 1, calling)
    assert len(calls) == 3 + jury.BREAKER  # two limited, an answer, then BREAKER in a row


def test_args_give_the_judge_no_tools_and_ask_for_the_schema() -> None:
    line = jury.args(JUDGE, "ref", "text")
    assert line[line.index("--tools") + 1] == ""
    assert line[line.index("--model") + 1] == JUDGE.model
    assert line[line.index("--effort") + 1] == JUDGE.effort
    assert json.loads(line[line.index("--json-schema") + 1]) == jury.SCHEMA
    assert "<reference>\nref\n</reference>" in line[2]
