import dataclasses
import pathlib
import tomllib

import pytest
from evals import calibrate
from evals.calibrate import Cell, Label, Stamp
from evals.suite import Judge, load_suite
from helpers import JUDGE, JUDGED, KEY, SUITE, write_suite

DASH, EMOJI, ACUTE = chr(0x2014), chr(0x1F600), chr(0xE9)


def test_the_wilson_bound_sets_the_bar_at_37_of_40() -> None:
    assert calibrate.wilson_lower(37, 40) >= calibrate.LOWER
    assert calibrate.wilson_lower(36, 40) < calibrate.LOWER
    assert calibrate.wilson_lower(0, 0) == 0.0
    assert calibrate.wilson_lower(40, 40) == pytest.approx(0.9124, abs=1e-4)


def test_kappa_against_hand_computed_matrices() -> None:
    # observed 75/90, chance 0.5 * 50/90 + 0.5 * 40/90 = 0.5
    assert calibrate.kappa(Cell("n", tp=40, fn=5, tn=35, fp=10)) == pytest.approx(2 / 3)
    # an always-yes judge on 80 positives and 20 negatives agrees 80% and scores nothing
    assert calibrate.kappa(Cell("n", tp=80, fp=20)) == pytest.approx(0.0)
    assert calibrate.kappa(Cell("n", tp=10)) is None
    assert calibrate.kappa(Cell("n")) is None


def test_fleiss_against_a_hand_computed_table() -> None:
    rows = [[True, True, True], [False, False, False], [True, True, False], [False, False, True]]
    assert calibrate.fleiss(rows) == pytest.approx(1 / 3)
    assert calibrate.fleiss([[True, True, True]] * 4) is None
    assert calibrate.fleiss([[True, False], [True]]) is None
    assert calibrate.fleiss([]) is None


def test_rates_and_cells() -> None:
    cell = Cell("natural", "old").add(True, True).add(True, False).add(False, False)
    assert (cell.tp, cell.fn, cell.tn, cell.fp, cell.n) == (1, 1, 1, 0, 3)
    assert (cell.tpr, cell.tnr) == (0.5, 1.0)
    assert Cell("x", tp=2).tnr is None


def cleared_stamp() -> Stamp:
    controls = [Cell(k, tn=10) for k in calibrate.CONTROL_KINDS]
    pairs = [Cell(k, tp=30, tn=30) for k in calibrate.INVARIANCE_KINDS]
    return Stamp(
        judge="flags",
        instrument="i1",
        versions=("i1",),
        labels="l1",
        labeller="claude-opus-5-5 xhigh",
        date="2026-10-27",
        cells=(
            Cell("natural", "none", tp=19, fn=1, tn=19, fp=1),
            Cell("natural", "old", tp=20, tn=20),
            Cell("sibling", tn=40),
            Cell("reference", tp=60, fn=1, tn=70, fp=1),
            *controls,
            *pairs,
        ),
        references={"c1": "h1"},
        gold_right=99,
        gold_n=100,
        labelled=100,
        unsure=10,
        fleiss=0.85,
    )


def failing(stamp: Stamp) -> list[str]:
    return [r.name for r in calibrate.rows(stamp) if r.status == "fail"]


def test_a_stamp_meeting_every_row_clears_the_bar() -> None:
    assert failing(cleared_stamp()) == []
    assert calibrate.cleared(cleared_stamp())


def swap(stamp: Stamp, kind: str, arm: str, cell: Cell) -> Stamp:
    cells = tuple(cell if (c.kind, c.arm) == (kind, arm) else c for c in stamp.cells)
    return dataclasses.replace(stamp, cells=cells)


@pytest.mark.parametrize(
    ("cell", "row"),
    [
        (Cell("natural", "old", tp=17, fn=3, tn=20), "1 TPR"),
        (Cell("natural", "old", tp=20, tn=17, fp=3), "2 TNR"),
        (Cell("natural", "old", tp=20, tn=19), "2 TNR"),
        (Cell("sibling", tn=39), "4 TNR, sibling"),
        (Cell("reference", tp=60, fn=2, tn=70, fp=1), "5 references"),
        (Cell("control-injection", tn=9, fp=1), "6 control-injection"),
        (Cell("control-empty", tn=9), "6 control-empty"),
        (Cell("invariance-minor", tp=28, tn=28, fp=4), "7 invariance-minor"),
        (Cell("invariance-format", tp=30, tn=29), "7 invariance-format"),
        (Cell("natural", "none", tp=16, fn=4, tn=20), "8 arm none"),
        # with the other arm, 88 of 100 positives: a Wilson lower bound over 0.80, a rate under 0.9
        (Cell("natural", "old", tp=69, fn=11, tn=20), "1 TPR"),
    ],
)
def test_each_counted_row_of_the_bar_can_fail_it(cell: Cell, row: str) -> None:
    stamp = swap(cleared_stamp(), cell.kind, cell.arm, cell)
    assert any(name.startswith(row) for name in failing(stamp)), failing(stamp)
    assert not calibrate.cleared(stamp)


@pytest.mark.parametrize(
    ("stamp", "row"),
    [
        (dataclasses.replace(cleared_stamp(), gold_right=97), "labellers on gold"),
        (dataclasses.replace(cleared_stamp(), fleiss=None), "labellers' Fleiss"),
        (dataclasses.replace(cleared_stamp(), fleiss=0.79), "labellers' Fleiss"),
        (dataclasses.replace(cleared_stamp(), unsure=11), "labelled unsure"),
    ],
)
def test_the_labelling_panel_can_fail_the_bar(stamp: Stamp, row: str) -> None:
    assert any(name.startswith(row) for name in failing(stamp)), failing(stamp)
    assert not calibrate.cleared(stamp)


def test_kappa_on_fewer_than_80_natural_items_fails() -> None:
    stamp = swap(cleared_stamp(), "natural", "old", Cell("natural", "old"))
    assert "3 kappa, natural items" in failing(stamp)


def test_kappa_below_the_bar_fails_while_both_rates_clear() -> None:
    # 420 positives and 60 negatives: TPR 0.950 and TNR 0.933 clear, kappa is 0.788
    skewed = Cell("natural", "old", tp=380, fn=20, tn=37, fp=3)
    stamp = swap(cleared_stamp(), "natural", "old", skewed)
    assert failing(stamp) == ["3 kappa, natural items"]


def test_a_dev_rate_over_held_out_warns_and_fails_nothing_itself() -> None:
    # held-out TPR 0.9 at least on a cleared stamp, so dev can exceed it by more than GAP
    # only when row 1 fails as well
    low = swap(cleared_stamp(), "natural", "old", Cell("natural", "old", tp=13, fn=7, tn=20))
    stamp = dataclasses.replace(low, cells=(*low.cells, Cell("dev", "old", tp=40, tn=40)))
    statuses = {r.name: r.status for r in calibrate.rows(stamp)}
    assert statuses["dev TPR over held-out"] == "warn"
    assert "dev TPR over held-out" not in failing(stamp)


def test_a_per_arm_j_gap_over_a_tenth_warns() -> None:
    stamp = swap(
        cleared_stamp(), "natural", "none", Cell("natural", "none", tp=18, fn=2, tn=17, fp=3)
    )
    warned = [r for r in calibrate.rows(stamp) if r.status == "warn"]
    assert [r.name for r in warned] == ["per-arm J gap"]
    assert calibrate.cleared(stamp)


def test_gates_only_on_a_current_stamp_that_cleared() -> None:
    stamp = cleared_stamp()
    assert calibrate.gates(stamp, "i1", {"c1": "h1"}, "l1") == ""
    assert calibrate.gates(stamp, "i1", {"c1": "h1", "c9": "new"}, "l1") == ""
    assert calibrate.gates(stamp, "i1", {}, "l1") == ""  # c1 removed
    assert calibrate.gates(None, "i1", {}, "l1") == "no calibration stamp"
    assert "another version" in calibrate.gates(stamp, "i2", {"c1": "h1"}, "l1")
    assert "labels changed" in calibrate.gates(stamp, "i1", {"c1": "h1"}, "l2")
    assert "reference of c1 changed" in calibrate.gates(stamp, "i1", {"c1": "h2"}, "l1")
    missed = dataclasses.replace(stamp, gold_right=0)
    assert "bar missed" in calibrate.gates(missed, "i1", {"c1": "h1"}, "l1")


def test_a_cleared_version_stale_by_labels_or_a_dev_reference_is_stamped_again() -> None:
    judge = Judge("flags", "Q?", held_out=("c2",))
    stamp = dataclasses.replace(cleared_stamp(), references={"c1": "h1", "c2": "h2"})
    refs = {"c1": "h1", "c2": "h2"}
    refusal = calibrate.held_out_refusal
    assert "scored on held-out already" in refusal(judge, stamp, "i1", refs, "l1")
    assert refusal(judge, stamp, "i1", refs, "l2") == ""
    assert refusal(judge, stamp, "i1", refs | {"c1": "h9"}, "l1") == ""
    assert "restore it" in refusal(judge, stamp, "i1", refs | {"c2": "h9"}, "l2")
    missed = dataclasses.replace(stamp, gold_right=0)
    assert "scored on held-out already" in refusal(judge, missed, "i1", refs, "l2")
    assert refusal(judge, stamp, "i2", refs, "l2") == ""


def test_a_stamp_lists_each_version_once() -> None:
    material = calibrate.Sources({}, {}, [])

    def stamped(instrument: str) -> Stamp:
        return calibrate.new_stamp(
            Judge("flags", "Q?"), instrument, cleared_stamp(), held=True, material=material,
            found=[], verdicts={}, single={}, split=(), gold=(0, 0), labels="l2", date="d",
        )  # fmt: skip

    assert stamped("i1").versions == ("i1",)
    assert stamped("i2").versions == ("i1", "i2")


def test_a_stamp_round_trips_and_a_broken_one_is_refused(tmp_path: pathlib.Path) -> None:
    path = tmp_path / "stamp.toml"
    stamp = dataclasses.replace(cleared_stamp(), burned=("k1",), human_audited=3)
    calibrate.write_stamp(path, stamp)
    assert calibrate.read_stamp(path) == stamp
    path.read_text().encode("ascii")
    calibrate.write_stamp(path, dataclasses.replace(stamp, fleiss=None))
    assert calibrate.read_stamp(path) == dataclasses.replace(stamp, fleiss=None)
    assert calibrate.read_stamp(tmp_path / "none.toml") is None
    path.write_text(path.read_text().replace("gold_n = 100", 'gold_n = "100"'))
    with pytest.raises(ValueError, match="not a stamp"):
        calibrate.read_stamp(path)


def test_toml_strings_stay_ascii_and_read_back() -> None:
    text = "Critical " + DASH + ' "quoted" \\ back\nslash\ttab \x01 ' + EMOJI + " " + ACUTE
    encoded = calibrate.toml_str(text)
    encoded.encode("ascii")
    assert tomllib.loads(f"v = {encoded}")["v"] == text
    assert tomllib.loads(f"v = {calibrate.toml_str('a' + chr(0xD800))}")["v"] == "a" + chr(0xFFFD)


def test_labels_round_trip_in_ascii(tmp_path: pathlib.Path) -> None:
    labels = [
        Label(
            "k1",
            "c1",
            "old",
            "claude-sonnet-5-5",
            "claude-opus-5-5 xhigh",
            ("yes", "yes", "no"),
            "yes",
            "a " + DASH + " b\n| x |",
        ),
        Label("k2", "c1", "none", "", "claude-opus-5-5 xhigh", ("no",) * 3, "no", ""),
    ]
    path = tmp_path / "labels" / "c1.toml"
    calibrate.write_labels(path, labels)
    path.read_text().encode("ascii")
    assert calibrate.read_labels(path) == labels
    assert calibrate.all_labels(tmp_path / "labels") == labels
    before = calibrate.labels_hash(tmp_path / "labels")
    calibrate.write_labels(path, labels[:1])
    assert calibrate.labels_hash(tmp_path / "labels") != before


def test_agreement_leaves_out_items_a_labeller_was_unsure_of() -> None:
    def lab(votes: tuple[str, ...], label: str) -> Label:
        return Label("k", "c", "old", "", "", votes, label, "")

    labels = [
        lab(("yes", "yes", "yes"), "yes"),
        lab(("no", "no", "no"), "no"),
        lab(("yes", "yes", "no"), "yes"),
        lab(("no", "no", "yes"), "no"),
        lab(("unsure", "yes", "yes"), "unsure"),
    ]
    fleiss, unsure = calibrate.agreement(labels)
    assert fleiss == pytest.approx(1 / 3)
    assert unsure == 1


def test_strip_format_drops_the_table_and_verdict_and_keeps_findings() -> None:
    report = "**Important**\n\n1. `a.py`: reimplements median.\n\n| Severity | Count |\n|---|---|\n| Important | 1 |\n\n**Verdict**: WARNING"
    stripped = calibrate.strip_format(report)
    assert "reimplements median" in stripped
    assert "|" not in stripped
    assert "Verdict" not in stripped
    assert calibrate.add_minor(report).startswith(report)
    assert "**Minor**" in calibrate.add_minor(report)


def test_a_reference_is_gold_only_when_the_judged_question_is_what_it_fails(
    tmp_path: pathlib.Path,
) -> None:
    root = write_suite(tmp_path, SUITE + JUDGE, KEY + JUDGED)
    refs = root / "cases" / "c1" / "reference"
    refs.mkdir()
    (refs / "pass-1.toml").write_text('commits = ["fix: y\\n\\nCloses #42"]\nfinal = "Done."\n')
    (refs / "fail-1.toml").write_text('commits = ["fix: y"]\nfinal = "Done."\n')
    (refs / "fail-2.toml").write_text('commits = ["fix: y\\n\\nCloses #42"]\nfinal = "Done."\n')
    case = load_suite(root).cases[0]
    by_name = {r.name: r for r in case.references}
    check = case.checks[-1]
    assert calibrate.reference_truth(case, by_name["pass-1"], "") is True
    assert calibrate.reference_truth(case, by_name["fail-1"], "") is None
    assert calibrate.reference_truth(case, by_name["fail-2"], "") is False
    # with the regex metric it replaces set aside, fail-1 fails only the judged question
    assert calibrate.reference_truth(case, by_name["fail-1"], "kept") is False
    assert calibrate.reference_text(check, by_name["fail-1"]) == "fix: y"


HELD = Judge("flags", "Q?", held_out=("a",), siblings=(("a", "b"),))


def label(key: str, case: str, value: str, arm: str = "old") -> Label:
    return Label(key, case, arm, "", "", (value,) * 3, value, f"report {key}")


def sources() -> calibrate.Sources:
    labels = [
        label("a1", "a", "yes"),
        label("a2", "a", "no", "none"),
        label("a3", "a", "unsure"),
        label("a4", "a", "yes"),
        label("b1", "b", "yes"),
        label("c1", "c", "yes"),
    ]
    gold = {"a": [("pass-1", "ref a", True)], "c": [("fail-1", "ref c", False)]}
    return calibrate.Sources({"a": "A", "b": "B", "c": "C"}, gold, labels, {"a1": True})


def test_held_out_items_follow_their_case_and_leave_burned_ones_to_dev() -> None:
    found = calibrate.items(HELD, "held-out", sources(), burned=("a4",))
    by_kind: dict[str, list[calibrate.Item]] = {}
    for item in found:
        by_kind.setdefault(item.kind, []).append(item)
    assert [(i.id, i.truth, i.compare) for i in by_kind["natural"]] == [
        ("a1", True, True),
        ("a2", False, None),
    ]
    assert {i.id for i in by_kind["dev"]} == {"a4", "b1", "c1"}
    assert "sibling" not in by_kind  # a's one sibling, b, is dev: no reference crosses sets
    assert [i.pair for i in by_kind["invariance-format"]] == ["a1", "a2"]
    assert [(i.case, i.truth) for i in by_kind["reference"]] == [("a", True)]
    assert len(by_kind["control-empty"]) == len(by_kind["control-unknown"]) == calibrate.CONTROLS
    # off-topic: a "yes" of a case outside the family, against this case's reference
    assert {(i.case, i.text) for i in by_kind["control-offtopic"]} == {("a", "report c1")}
    assert all(
        i.text.endswith(calibrate.INJECTION) and i.case == "a" for i in by_kind["control-injection"]
    )
    assert all(i.truth is False for k in calibrate.CONTROL_KINDS for i in by_kind[k])
    assert calibrate.items(HELD, "held-out", sources()) == calibrate.items(
        HELD, "held-out", sources()
    )


def test_dev_items_take_the_other_cases_and_no_dev_kind() -> None:
    found = calibrate.items(HELD, "dev", sources(), burned=("a4",))
    natural = {i.id for i in found if i.kind == "natural"}
    assert natural == {"a4", "b1", "c1"}
    assert not [i for i in found if i.kind == "dev"]
    assert [(i.case, i.truth) for i in found if i.kind == "reference"] == [("c", False)]


def test_sibling_swaps_stay_within_their_set() -> None:
    judge = Judge("flags", "Q?", held_out=("a", "b"), siblings=(("a", "b", "c", "d"),))
    labels = [label("a1", "a", "yes"), label("b1", "b", "no"), label("c1", "c", "yes")]
    material = calibrate.Sources({k: k.upper() for k in "abcd"}, {}, labels)
    held = [i for i in calibrate.items(judge, "held-out", material) if i.kind == "sibling"]
    assert [(i.id, i.case, i.text) for i in held] == [
        ("sibling:a1", "b", "report a1"),
        ("sibling:b1", "a", "report b1"),
    ]
    dev = [i for i in calibrate.items(judge, "dev", material) if i.kind == "sibling"]
    assert [(i.id, i.case) for i in dev] == [("sibling:c1", "d")]


def test_cells_count_by_arm_and_score_invariance_against_the_pair() -> None:
    found = calibrate.items(HELD, "held-out", sources())
    judged = {i.id: i.truth is True for i in found if not i.pair} | {"a2": True}
    judged |= {i.id: judged[i.pair] for i in found if i.pair}
    judged["invariance-minor:a1"] = False  # the answer flipped when Minor findings were added
    cells = {
        (c.kind, c.arm): c
        for c in calibrate.cells(found, judged, {"a1": False, "a2": False, "a4": True})
    }
    assert cells["natural", "old"] == Cell("natural", "old", tp=2)
    assert cells["natural", "none"] == Cell("natural", "none", fp=1)
    assert cells["invariance-minor", ""] == Cell("invariance-minor", "", tp=2, fn=1)
    assert cells["single", ""] == Cell("single", "", tp=1, fn=1, tn=1)
    assert cells["compare", ""] == Cell("compare", "", tp=1)


def test_standing_reads_the_tracked_stamp_and_names_what_went_stale(tmp_path: pathlib.Path) -> None:
    root = write_suite(tmp_path, SUITE + JUDGE, KEY + JUDGED)
    suite = load_suite(root)
    judge = suite.judges["flags"]
    assert calibrate.standing(root, suite.cases, judge, "i1").why_not == "no calibration stamp"
    folder = calibrate.judge_dir(root, "flags")
    stamp = dataclasses.replace(
        cleared_stamp(),
        references={"c1": calibrate.text_hash("Issue 42.")},
        labels=calibrate.labels_hash(folder / "labels"),
    )
    calibrate.write_stamp(folder / "stamp.toml", stamp)
    assert calibrate.standing(root, suite.cases, judge, "i1") == calibrate.Standing(stamp, "", "")
    later = calibrate.standing(root, suite.cases, judge, "i2")
    assert later.stale == later.why_not == "the stamp is for another version of the judge"
    (folder / "stamp.toml").write_text("judge = 1\n")
    broken = calibrate.standing(root, suite.cases, judge, "i1")
    assert "not a stamp" in broken.stale
    assert broken.why_not == broken.stale


def test_j_is_tpr_plus_tnr_minus_one_on_natural_items() -> None:
    assert calibrate.j_of(cleared_stamp()) == pytest.approx(39 / 40 + 39 / 40 - 1)
    assert calibrate.j_of(dataclasses.replace(cleared_stamp(), cells=())) is None
