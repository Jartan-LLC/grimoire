import argparse
import dataclasses
import json
import pathlib
import shutil
import sys
from typing import cast

import eval as cli
import pytest
from evals import cache, calibrate, jury, session
from evals.arms import Arm
from evals.plan import Listed, Plan
from evals.suite import Suite, load_suite
from evals.verdict import MetricVerdict
from helpers import JUDGE, JUDGED, KEY, SUITE, write_suite


def test_record_baseline_replaces_only_its_own_model_and_arm(tmp_path: pathlib.Path) -> None:
    key = tmp_path / "key.toml"
    key.write_text('split = "dev"\n\n[[check]]\nmetric = "kept"\n')
    cli.record_baseline(key, "claude-opus-5-5", "none", 3, 3)
    cli.record_baseline(key, "claude-haiku-5-5", "none", 1, 3)
    cli.record_baseline(key, "claude-opus-5-5", "none", 2, 3)
    text = key.read_text()
    assert text.count("[[baseline]]") == 2
    assert 'model = "claude-opus-5-5"\narm = "none"\nfailures = 2\n' in text
    assert 'model = "claude-haiku-5-5"\narm = "none"\nfailures = 1\n' in text
    assert text.startswith('split = "dev"\n\n[[check]]')


def test_a_remote_cases_baseline_records_the_remote_runner(tmp_path: pathlib.Path) -> None:
    root = write_suite(tmp_path, key="remote = true\n" + KEY)
    key = root / "cases" / "c1" / "key.toml"
    cli.record_baseline(key, "claude-opus-5-5", "old", 1, 3, remote=True)
    assert (
        f"runner = {session.RUNNER}\nremote_runner = {session.REMOTE_RUNNER}\n" in key.read_text()
    )
    (baseline,) = load_suite(root).cases[0].baselines
    assert (baseline.failures, baseline.remote_runner) == (1, session.REMOTE_RUNNER)
    cli.record_baseline(key, "claude-opus-5-5", "old", 2, 3)
    assert "remote_runner" not in key.read_text()


def test_a_watch_model_reports_harm_without_failing_a_bar(tmp_path: pathlib.Path) -> None:
    suite = load_suite(
        write_suite(
            tmp_path,
            SUITE + '\n[[metric]]\nid = "no_exploit"\ndirection = "higher"\nmust_hold = true\n',
        )
    )
    verdicts = {
        "kept": MetricVerdict("kept", 6, 1, 0.5, 0, 3, 1, 0.01, "WORSE"),
        "no_exploit": MetricVerdict("no_exploit", 2, 1, 0.9, 0, 1, 1, 0.5, "WORSE", must_hold=True),
    }
    gate = cli.report(suite, verdicts, "HURT", watch=False)
    watch = cli.report(suite, verdicts, "HURT", watch=True)
    assert [line.split(":")[0] for line in gate[:2]] == ["FAILED", "FAILED"]
    assert watch[0].startswith("REPORT: kept WORSE")
    assert watch[1].startswith("STANDING: no_exploit WORSE")
    assert any(line.startswith("Result (watch model, advisory") for line in watch)


def test_a_reported_metric_never_prints_as_a_failed_bar(tmp_path: pathlib.Path) -> None:
    suite = load_suite(
        write_suite(tmp_path, SUITE + '\n[[metric]]\nid = "noted"\ndirection = "higher"\n')
    )
    verdicts = {"noted": MetricVerdict("noted", 8, 1, 0.2, 0, 7, 1, 0.004, "WORSE")}
    assert cli.report(suite, verdicts, "SHIP", watch=False)[0].startswith("REPORT: noted")


def test_screens_on_two_models_keep_their_own_plans_and_alternate_which_arm_starts(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    suite = load_suite(
        write_suite(
            tmp_path / "suite", 'models = ["claude-opus-5-5", "claude-sonnet-5-5"]\n' + SUITE
        )
    )
    store = tmp_path / "store"
    orders: list[list[str]] = []

    def arm(name: str, *_: object) -> Arm:
        return Arm(name, "h", {})

    def run(work: list[cli.Work], _: int) -> list[cli.Work]:
        orders.append([w[1].name for w in work])
        return work

    def branch(*_: str) -> str:
        return "feature/x\n"

    def nothing(*_: object) -> None:
        return None

    monkeypatch.setattr(cli, "build_arm", arm)
    monkeypatch.setattr(cli, "git", branch)
    monkeypatch.setattr(cli, "run_samples", run)
    monkeypatch.setattr(cli, "decide", nothing)
    args = argparse.Namespace(
        split="dev", base="main", new_ref=None, samples=2, trial="", new_plan=False, jobs=1
    )
    for model in ("claude-opus-5-5", "claude-sonnet-5-5", "claude-opus-5-5"):
        spec = session.Spec(model, "2.1.310", 1.0, tmp_path, store)
        assert cli.screen(args, suite, spec, store) == 0
    assert len(list((store / "plans").iterdir())) == 2
    assert orders[0] == ["old", "new", "new", "old"]


def test_the_read_list_names_a_must_hold_failure_the_primary_passes(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    suite = load_suite(
        write_suite(
            tmp_path,
            SUITE + '\n[[metric]]\nid = "no_exploit"\ndirection = "higher"\nmust_hold = true\n',
        )
    )
    leak = cache.Sample("k1", "c1", "new", 0, {}, True, [], [], "", {}, {})
    clean = cache.Sample("k2", "c1", "new", 1, {}, True, [], [], "", {}, {})
    scores = {"k1": {"kept": 1.0, "no_exploit": 0.0}, "k2": {"kept": 1.0, "no_exploit": 1.0}}

    def sample_scores(_: object, sample: cache.Sample, __: object) -> dict[str, float]:
        return scores[sample.key]

    monkeypatch.setattr(cli, "sample_scores", sample_scores)
    verdicts = {
        "kept": MetricVerdict("kept", 1, 1, 1, 0, 0, 1, 1, "INCONCLUSIVE"),
        "no_exploit": MetricVerdict("no_exploit", 1, 1, 0.5, 0, 1, 1, 1, "WORSE", must_hold=True),
    }
    lines = cli.to_read(suite, {"new": [leak, clean]}, {"new": {}, "old": {}}, verdicts, tmp_path)
    assert "- new c1 #0 fails no_exploit: k1" in lines
    assert not any("k2" in line and "fails" in line for line in lines)


def test_a_plan_names_the_arms_plugins_alike_wherever_the_store_is(tmp_path: pathlib.Path) -> None:
    suite = load_suite(write_suite(tmp_path / "suite"))
    plans: list[dict[str, object]] = []
    for store in (tmp_path / "a", tmp_path / "b"):
        old = Arm("old", "h", {"gitwise": str(store / "arms" / "old-1" / "plugins" / "gitwise")})
        spec = session.Spec("claude-opus-5-5", "2.1.310", 1.0, tmp_path, store)
        plans.append(cli.pinned(suite, "dev", 3, spec, old))
    assert plans[0] == plans[1]
    assert "<arm>/plugins/gitwise" in cast("list[str]", plans[0]["flags"])


def test_a_screens_identity_holds_the_trial_the_new_arm_and_each_cases_hash(
    tmp_path: pathlib.Path,
) -> None:
    root = write_suite(tmp_path)
    cases = load_suite(root).cases
    plan: dict[str, object] = {"suite": "a", "samples": 3}
    arms = {"old": Arm("old", "o", {}), "new": Arm("new", "n", {})}
    base = cli.drawn(list(cases), plan, arms, "t1")
    assert cli.drawn(list(cases), plan | {"suite": "b"}, arms, "t1") == base
    assert cli.drawn(list(cases), plan, arms, "t2") != base
    assert cli.drawn(list(cases), plan, arms | {"new": Arm("new", "n2", {})}, "t1") != base
    (root / "cases" / "c1" / "prompt.md").write_text("Fix issue 43 and commit.\n")
    assert cli.drawn(list(load_suite(root).cases), plan, arms, "t1") != base


def test_each_drawn_sample_prints_its_key(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    (case,) = load_suite(write_suite(tmp_path)).cases

    def drawn_sample(case: cli.Case, arm: Arm, index: int, *_: object) -> cache.Sample:
        return cache.Sample(
            "k" + str(index), case.id, arm.name, index, {}, True, [], [], "", {}, {}
        )

    def nothing() -> None:
        return None

    monkeypatch.setattr(session, "preflight", nothing)
    monkeypatch.setattr(session, "run_sample", drawn_sample)
    spec = session.Spec("claude-opus-5-5", "2.1.310", 1.0, tmp_path, tmp_path / "store")
    cli.run_samples([(case, Arm("old", "h", {}), 3, spec)], 1)
    assert capsys.readouterr().out == "  old c1 #3: ok: k3\n"


def test_a_screen_under_a_changed_plan_runs_nothing_until_a_new_plan(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    suite = load_suite(write_suite(tmp_path / "suite"))
    store = tmp_path / "store"
    ran: list[int] = []
    old_hash = ["o1"]

    def arm(name: str, *_: object) -> Arm:
        return Arm(name, old_hash[0] if name == "old" else "n", {})

    def run(work: list[cli.Work], _: int) -> list[cli.Work]:
        ran.append(len(work))
        return work

    def branch(*_: str) -> str:
        return "feature/x\n"

    def nothing(*_: object) -> None:
        return None

    monkeypatch.setattr(cli, "build_arm", arm)
    monkeypatch.setattr(cli, "git", branch)
    monkeypatch.setattr(cli, "run_samples", run)
    monkeypatch.setattr(cli, "decide", nothing)
    spec = session.Spec("claude-opus-5-5", "2.1.310", 1.0, tmp_path, store)

    def screen(samples: int, new_plan: bool = False) -> int:
        args = argparse.Namespace(
            split="dev", base="main", new_ref=None, samples=samples, trial="",
            new_plan=new_plan, jobs=1,
        )  # fmt: skip
        return cli.screen(args, suite, spec, store)

    assert screen(2) == 0
    assert screen(3) == 1
    old_hash[0] = "o2"
    assert screen(2) == 1
    assert len(ran) == 1
    assert screen(3, new_plan=True) == 0
    assert len(ran) == 2


def power_suite(
    root: pathlib.Path, units: int, rates: dict[str, tuple[int | None, int | None]], watch: str = ""
) -> Suite:
    """`units` cases on each held-out split; `rates` maps a model to its (old, none) failures of 3."""
    models = ", ".join(f'"{m}"' for m in rates)
    header = f"models = [{models}]\n" + (f'watch = ["{watch}"]\n' if watch else "")
    write_suite(root, header + SUITE.replace('rule = "better"', 'rule = "no-regression"'))
    (root / "cases" / "c1").rename(root / "cases" / "template")
    template = root / "cases" / "template"
    for split in ("screen", "confirm"):
        for n in range(units):
            case = root / "cases" / f"{split}-{n}"
            shutil.copytree(template, case)
            key = KEY.split("[[baseline]]")[0].replace('split = "dev"', f'split = "{split}"')
            key = key.replace('kind = "target"', 'kind = "regression"')
            for model, (old, none) in rates.items():
                for arm, failures in (("old", old), ("none", none)):
                    if failures is not None:
                        key += f'\n[[baseline]]\nmodel = "{model}"\narm = "{arm}"\nfailures = {failures}\nruns = 3\nrunner = 2\n'
            (case / "key.toml").write_text(key)
    shutil.rmtree(template)
    return load_suite(root)


def test_the_planner_passes_a_split_the_control_moves_and_flags_one_it_does_not(
    tmp_path: pathlib.Path,
) -> None:
    lines, weak = cli.split_report(power_suite(tmp_path / "a", 8, {"claude-opus-5-5": (0, 3)}))
    assert not weak
    assert "comes out WORSE 100%" in "\n".join(lines)
    unmoved: list[dict[str, tuple[int | None, int | None]]] = [
        {"claude-opus-5-5": (0, 0)},
        {"claude-opus-5-5": (0, None)},
    ]
    for n, rates in enumerate(unmoved):
        _, weak = cli.split_report(power_suite(tmp_path / f"u{n}", 8, rates))
        assert weak


def test_the_planner_lets_a_weak_watch_model_pass_and_flags_too_few_units(
    tmp_path: pathlib.Path,
) -> None:
    rates: dict[str, tuple[int | None, int | None]] = {
        "claude-opus-5-5": (0, 3),
        "claude-haiku-5-5": (1, 1),
    }
    lines, weak = cli.split_report(power_suite(tmp_path / "w", 8, rates, watch="claude-haiku-5-5"))
    assert not weak
    assert any(
        "claude-haiku-5-5" in line and "watch model: does not gate" in line for line in lines
    )
    lines, weak = cli.split_report(power_suite(tmp_path / "f", 2, {"claude-opus-5-5": (0, 3)}))
    assert weak
    assert any("too few units" in line for line in lines)


def test_the_planner_skips_the_control_only_for_a_target_old_does_not_hold(
    tmp_path: pathlib.Path,
) -> None:
    both: dict[str, tuple[int | None, int | None]] = {"claude-opus-5-5": (3, 3)}
    lines, weak = cli.split_report(power_suite(tmp_path / "new", 8, both), old_holds_target=False)
    assert not weak
    assert any("no positive control" in line for line in lines)
    unrecorded: dict[str, tuple[int | None, int | None]] = {"claude-opus-5-5": (None, None)}
    lines, weak = cli.split_report(power_suite(tmp_path / "bare", 8, unrecorded))
    assert weak
    assert any("no old or no none baselines" in line for line in lines)


def test_the_planner_sizes_a_split_by_the_units_its_ruled_metrics_score(
    tmp_path: pathlib.Path,
) -> None:
    rates: dict[str, tuple[int | None, int | None]] = {"claude-opus-5-5": (0, 3)}
    power_suite(tmp_path, 8, rates)
    for split in ("screen", "confirm"):
        for n in range(2, 8):
            key = tmp_path / "cases" / f"{split}-{n}" / "key.toml"
            key.write_text(key.read_text().replace('metric = "kept"', 'metric = "delivered"'))
    lines, weak = cli.split_report(load_suite(tmp_path))
    assert weak
    assert any("2 scored by every metric" in line for line in lines)
    assert any("too few units" in line for line in lines)


UNCOVERED = "plugins/gitwise/skills/github-conventions/SKILL.md"
STEPS = ("  first", "  next", "  then", "  indirect", "  nothing", "smoke test", "UNCOVERED")


def reach(root: pathlib.Path, rates: tuple[int, int] = (0, 3)) -> tuple[Plan, str, str]:
    """A plan reaching a direct and an indirect suite and one uncovered file; and the suites' paths.

    Each suite runs on opus and on haiku, a watch model, and has confirm cases.
    """
    both: dict[str, tuple[int | None, int | None]] = {
        "claude-haiku-5-5": rates,
        "claude-opus-5-5": rates,
    }
    direct = power_suite(root / "direct", 8, both, watch="claude-haiku-5-5")
    indirect = power_suite(root / "indirect", 8, both, watch="claude-haiku-5-5")
    plan = Plan(
        [Listed(direct, ["d.md"], direct=True), Listed(indirect, ["i.md"], direct=False)],
        [UNCOVERED],
        [],
    )
    return plan, str(direct.path), str(indirect.path)


def planned(
    plan: Plan,
    tier: int | None,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> tuple[int, list[str]]:
    """`plan_command`'s exit code and output lines for `plan` at `tier`."""

    def make_plan(root: pathlib.Path, base: str) -> Plan:
        return plan

    def holds(target: str, base: str) -> bool:
        return True

    monkeypatch.setattr(cli, "make_plan", make_plan)
    monkeypatch.setattr(cli, "old_holds", holds)
    code = cli.plan_command("main", tier)
    return code, capsys.readouterr().out.splitlines()


def test_the_plan_without_a_tier_lists_what_the_change_reaches_and_asks_for_one(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    plan, direct, indirect = reach(tmp_path)
    code, lines = planned(plan, None, monkeypatch, capsys)
    assert code == 0
    assert lines[:3] == [
        f"{direct}: DIRECT, covers d.md",
        f"{indirect}: INDIRECT, covers i.md",
        f"UNCOVERED: {UNCOVERED}",
    ]
    assert len(lines) == 4
    assert "TIER=<n>" in lines[3]


def test_the_plan_at_tier_1_lists_what_the_change_reaches_with_no_steps(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    plan, direct, indirect = reach(tmp_path)
    assert planned(plan, 1, monkeypatch, capsys) == (
        0,
        [
            f"{direct}: DIRECT, covers d.md",
            f"{indirect}: INDIRECT, covers i.md",
            f"UNCOVERED: {UNCOVERED}",
            "no eval is due if nothing this change alters reaches the model",
        ],
    )


def test_the_plan_at_tier_2_screens_direct_suites_and_reports_their_screen_split_unadvised(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    plan, direct, _ = reach(tmp_path, rates=(0, 0))
    code, lines = planned(plan, 2, monkeypatch, capsys)
    assert code == 0
    assert "  what its screen split can see (say in the PR what it shows):" in lines
    assert any(line.startswith("  screen: ") for line in lines)
    assert not any(line.startswith("  confirm: ") for line in lines)
    assert sum(line.startswith("  screen: ") for line in lines) == 1
    assert any("no sample count up to 10 reaches 80%" in line for line in lines)
    assert not any("add cases" in line for line in lines)
    assert [line for line in lines if line.startswith(STEPS)] == [
        f"  next: make eval-screen SUITE={direct} MODEL=claude-haiku-5-5 (watch model: advisory)",
        f"  next: make eval-screen SUITE={direct} MODEL=claude-opus-5-5",
        "  nothing to run",
        f"UNCOVERED: {UNCOVERED} -- name it in the PR as covered by no suite",
    ]


def test_the_plan_at_tier_3_also_screens_each_indirect_suite_once_and_asks_for_a_smoke_test(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    plan, direct, indirect = reach(tmp_path)
    code, lines = planned(plan, 3, monkeypatch, capsys)
    assert code == 0
    assert "  what its screen split can see (say in the PR what it shows):" in lines
    assert [line for line in lines if line.startswith(STEPS)] == [
        f"  next: make eval-screen SUITE={direct} MODEL=claude-haiku-5-5 (watch model: advisory)",
        f"  next: make eval-screen SUITE={direct} MODEL=claude-opus-5-5",
        f"  next: make eval-screen SUITE={indirect} MODEL=claude-opus-5-5",
        "  indirect: screen only, on one gate model",
        'smoke test: write one ("Smoke tests" in tests/evals/README.md)',
        f"UNCOVERED: {UNCOVERED} -- cover it in the smoke test",
    ]
    haiku: dict[str, tuple[int | None, int | None]] = {"claude-haiku-5-5": (0, 3)}
    all_watch = power_suite(tmp_path / "w", 8, haiku, watch="claude-haiku-5-5")
    assert cli.next_steps(Listed(all_watch, ["x"], direct=False), "s", 3) == [
        "  next: make eval-screen SUITE=s MODEL=claude-haiku-5-5 (watch model: advisory)",
        "  indirect: screen only, on its first model (all are watch models: advisory)",
    ]


def test_the_plan_at_tier_4_advises_on_the_report_confirms_and_asks_for_a_suite(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    plan, direct, indirect = reach(tmp_path, rates=(0, 0))
    _, lines = planned(plan, 4, monkeypatch, capsys)
    assert "  what its splits can see:" in lines
    assert any(line.startswith("  confirm: ") for line in lines)
    assert any("reaches 80%: add cases the target changes" in line for line in lines)
    assert [line for line in lines if line.startswith(STEPS)] == [
        '  first: add cases the changed text affects ("Choosing cases" in tests/evals/README.md)',
        f"  next: make eval-screen SUITE={direct} MODEL=claude-haiku-5-5 (watch model: advisory)",
        f"  next: make eval-screen SUITE={direct} MODEL=claude-opus-5-5",
        "  then, before the PR: each of those again with SPLIT=confirm",
        f"  next: make eval-screen SUITE={indirect} MODEL=claude-opus-5-5",
        "  indirect: screen only, on one gate model",
        f"UNCOVERED: {UNCOVERED} -- write or extend a suite to cover it",
    ]
    for case in (tmp_path / "direct" / "cases").glob("confirm-*"):
        shutil.rmtree(case)
    no_confirm = Listed(load_suite(tmp_path / "direct"), ["x"], direct=True)
    assert cli.next_steps(no_confirm, "s", 4)[1] == (
        '  first: write confirm cases ("Splits" in tests/evals/README.md)'
    )
    code, lines = planned(Plan([no_confirm], [], []), 4, monkeypatch, capsys)
    assert code == 1
    assert "  confirm: no cases" in lines


def test_the_plan_fails_on_a_broken_suite_at_any_tier_and_on_a_weak_or_missing_one_at_tier_4(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    weak = power_suite(tmp_path, 8, {"claude-opus-5-5": (0, 0)})
    assert cli.split_report(weak)[1]
    broken = Plan([], [UNCOVERED], ["bad: no suite.toml"])
    for tier in (None, 1, 2, 3, 4):
        code, lines = planned(broken, tier, monkeypatch, capsys)
        assert (code, lines[0]) == (1, "BROKEN SUITE: bad: no suite.toml")
    for direct, tier, code in [(True, 2, 0), (True, 3, 0), (True, 4, 1), (False, 4, 0)]:
        plan = Plan([Listed(weak, ["x"], direct=direct)], [], [])
        assert planned(plan, tier, monkeypatch, capsys)[0] == code
    for tier, code in [(2, 0), (3, 0), (4, 1)]:
        assert planned(Plan([], [UNCOVERED], []), tier, monkeypatch, capsys)[0] == code


def test_eval_size_still_advises_on_a_weak_split_and_fails(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    unrecorded: dict[str, tuple[int | None, int | None]] = {"claude-opus-5-5": (None, None)}
    power_suite(tmp_path, 2, unrecorded)

    def holds(target: str, base: str) -> bool:
        return True

    monkeypatch.setattr(cli, "old_holds", holds)
    monkeypatch.setattr(sys, "argv", ["eval.py", "size", str(tmp_path)])
    assert cli.main() == 1
    out = capsys.readouterr().out
    assert "too few units for any verdict; add cases" in out
    assert "no old or no none baselines on this split; record them" in out


def test_a_plan_pins_the_judges_without_redrawing_sessions_when_they_change(
    tmp_path: pathlib.Path,
) -> None:
    plain = load_suite(write_suite(tmp_path / "plain"))
    judged = load_suite(write_suite(tmp_path / "judged", SUITE + JUDGE, KEY + JUDGED))
    old = Arm("old", "h", {})
    spec = session.Spec("claude-opus-5-5", "2.1.310", 1.0, tmp_path, tmp_path / "store")
    assert "judges" not in cli.pinned(plain, "dev", 3, spec, old)
    plan = cli.pinned(judged, "dev", 3, spec, old)
    assert plan["judges"] == {"flags": jury.instrument(judged.judges["flags"])}
    arms = {"old": old, "new": Arm("new", "n", {})}
    base = cli.drawn(list(judged.cases), plan, arms, "t1")
    assert cli.drawn(list(judged.cases), plan | {"judges": {"flags": "other"}}, arms, "t1") == base


def test_a_judge_without_a_cleared_stamp_gates_nothing(tmp_path: pathlib.Path) -> None:
    suite = load_suite(write_suite(tmp_path, SUITE + JUDGE, KEY + JUDGED))
    assert cli.advisory(suite) == {"flags": "no calibration stamp"}
    assert [m.id for m in cli.judged_metrics(suite)] == ["kept", "delivered", "kept@flags"]
    judge = suite.judges["flags"]
    folder = calibrate.judge_dir(suite.path, "flags")
    missed = calibrate.Stamp(
        judge="flags",
        instrument=jury.instrument(judge),
        versions=(jury.instrument(judge),),
        labels=calibrate.labels_hash(folder / "labels"),
        labeller="claude-opus-5-5 xhigh",
        date="2026-10-27",
        cells=(),
        references={"c1": calibrate.text_hash("Issue 42.")},
    )
    calibrate.write_stamp(folder / "stamp.toml", missed)
    assert "bar missed" in cli.advisory(suite)["flags"]
    cells = (
        calibrate.Cell("natural", "old", tp=38, fn=2, tn=40),
        calibrate.Cell("sibling", tn=40),
        calibrate.Cell("reference", tp=1),
        *(calibrate.Cell(k, tn=10) for k in calibrate.CONTROL_KINDS),
        *(calibrate.Cell(k, tp=60) for k in calibrate.INVARIANCE_KINDS),
    )
    cleared = dataclasses.replace(
        missed, cells=cells, gold_right=10, gold_n=10, labelled=10, fleiss=0.9
    )
    calibrate.write_stamp(folder / "stamp.toml", cleared)
    assert cli.advisory(suite) == {}
    assert [m.id for m in cli.judged_metrics(suite)] == ["kept", "delivered"]
    # J = 0.95 + 1.0 - 1: a harm the split sees at 0.38 is 0.40 on the true scale
    (line,) = cli._judged_scale(suite, 0.38)  # pyright: ignore[reportPrivateUsage]
    assert "J = 0.95; that harm is 0.40 on the true scale" in line


def test_align_scores_held_out_once_per_version_and_burns_a_missed_one(
    tmp_path: pathlib.Path, monkeypatch: pytest.MonkeyPatch, capsys: pytest.CaptureFixture[str]
) -> None:
    held = JUDGE.replace("question", 'held_out = ["c1"]\nquestion')
    suite = load_suite(write_suite(tmp_path / "suite", SUITE + held, KEY + JUDGED))
    judge = suite.judges["flags"]
    labels = calibrate.judge_dir(suite.path, "flags") / "labels" / "c1.toml"
    calibrate.write_labels(
        labels,
        [
            calibrate.Label("k1", "c1", "old", "", "m e", ("yes",) * 3, "yes", "fix: Closes #42"),
            calibrate.Label("k2", "c1", "none", "", "m e", ("no",) * 3, "no", "fix: y"),
        ],
    )
    calls: list[str] = []

    def says_no(j: object, reference: str, text: str) -> tuple[jury.Answer, str]:
        calls.append(text)
        usage: dict[str, object] = {judge.model: {}}
        return jury.Answer("no", ""), json.dumps({"modelUsage": usage, "structured_output": {}})

    monkeypatch.setattr(jury, "call", says_no)
    args = argparse.Namespace(set="held-out", jobs=1, labeller_model="m", labeller_effort="e")
    store = tmp_path / "store"
    assert cli.align(args, suite, judge, store) == 1  # an always-no judge misses the bar
    stamp = calibrate.read_stamp(labels.parent.parent / "stamp.toml")
    assert stamp is not None
    assert stamp.versions == (jury.instrument(judge),)
    assert stamp.burned == ("k1", "k2")
    assert stamp.cell("natural") == calibrate.Cell("natural", tp=0, fn=1, tn=1, fp=0)
    assert "MISSED" in capsys.readouterr().out
    with pytest.raises(SystemExit, match="scored on held-out already"):
        cli.align(args, suite, judge, store)
    before = len(calls)
    args.set = "dev"
    assert cli.align(args, suite, judge, store) == 0
    assert len(calls) == before  # every answer was kept
    assert "disagrees: natural c1 old True (no, no, no): k1" in capsys.readouterr().out
    assert calibrate.read_stamp(labels.parent.parent / "stamp.toml") == stamp
