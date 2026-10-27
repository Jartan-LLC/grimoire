import argparse
import pathlib
import shutil
from typing import cast

import eval as cli
import pytest
from evals import cache, session
from evals.arms import Arm
from evals.suite import Suite, load_suite
from evals.verdict import MetricVerdict
from helpers import KEY, SUITE, write_suite


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
