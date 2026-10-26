import itertools

import pytest
from evals.suite import Metric, PassRule
from evals.verdict import (
    MetricVerdict,
    compare,
    control_power,
    detectable_effect,
    judge,
    overall,
    sign_flip_p,
    smallest_p,
    unit_diffs,
)

UP = Metric("kept", "higher")
GUARD = Metric("bugs", "higher", margin=0.2)
MUST = Metric("no_exploit", "higher", must_hold=True)


def brute_force(diffs: list[float]) -> tuple[float, float]:
    sums = [
        sum(s * d for s, d in zip(signs, diffs, strict=True))
        for signs in itertools.product((1, -1), repeat=len(diffs))
    ]
    observed = sum(diffs)
    return (
        sum(t >= observed - 1e-12 for t in sums) / len(sums),
        sum(t <= observed + 1e-12 for t in sums) / len(sums),
    )


@pytest.mark.parametrize(
    "diffs",
    [
        [1.0] * 6,
        [1.0, 0.5, -0.5, 1.0, 0.0, 1 / 3],
        [-1.0, -1.0, 0.0, 2 / 3, -1 / 3],
        [0.25, -0.75, 0.5],
    ],
)
def test_sign_flip_p_matches_brute_force(diffs: list[float]) -> None:
    assert sign_flip_p(diffs) == pytest.approx(brute_force(diffs))


def test_six_units_all_better_reach_one_in_sixty_four() -> None:
    assert sign_flip_p([1.0] * 6) == (1 / 64, 1.0)
    assert smallest_p(6) == 1 / 64


def test_unit_diffs_are_new_minus_old_and_skip_units_one_arm_lacks() -> None:
    old = {"a": [0.0, 0.0], "b": [1.0], "c": [1.0]}
    new = {"a": [1.0, 0.0], "b": [0.0], "d": [1.0]}
    assert unit_diffs(old, new) == [0.5, -1.0]


def units(values: list[float], samples: int = 3) -> dict[str, list[float]]:
    return {str(i): [v] * samples for i, v in enumerate(values)}


def test_primary_is_better_when_every_unit_gains() -> None:
    v = compare(UP, units([0.0] * 6), units([1.0] * 6), guard=False)
    assert (v.verdict, v.gains, v.regressions, v.units) == ("BETTER", 6, 0, 6)


def test_four_units_can_never_reach_alpha() -> None:
    assert compare(UP, units([0.0] * 4), units([1.0] * 4), guard=False).verdict == "INCONCLUSIVE"


def test_primary_is_worse_when_every_unit_regresses() -> None:
    assert compare(UP, units([1.0] * 6), units([0.0] * 6), guard=False).verdict == "WORSE"


def test_mixed_units_are_inconclusive() -> None:
    v = compare(
        UP,
        units([0.0, 1.0, 0.0, 1.0, 0.0, 1.0]),
        units([1.0, 0.0, 1.0, 0.0, 1.0, 0.0]),
        guard=False,
    )
    assert (v.verdict, v.gains, v.regressions) == ("INCONCLUSIVE", 3, 3)


def test_a_guard_passes_only_when_harm_is_shown_inside_the_margin() -> None:
    assert compare(GUARD, units([1.0] * 6), units([1.0] * 6), guard=True).verdict == "PASS"
    assert compare(GUARD, units([1.0] * 3), units([1.0] * 3), guard=True).verdict == "INCONCLUSIVE"


def test_a_guard_catches_harm_at_the_plain_alpha() -> None:
    v = compare(GUARD, units([1.0] * 6), units([0.0] * 6), guard=True)
    assert v.verdict == "WORSE"
    assert v.p_worse == 1 / 64


def test_a_must_hold_metric_fails_on_one_failing_new_sample_whatever_old_did() -> None:
    new = units([1.0] * 6)
    new["0"] = [1.0, 0.0, 1.0]
    assert compare(MUST, units([0.0] * 6), new, guard=True).verdict == "WORSE"


def verdicts(**by_metric: str) -> dict[str, MetricVerdict]:
    return {
        m: MetricVerdict(m, 6, 0, 0, 0, 0, 1, 1, v, must_hold=m == "no_exploit")
        for m, v in by_metric.items()
    }


BETTER_RULE = PassRule("kept", "better", ("bugs",), 0.3, 3)
SAFE_RULE = PassRule("kept", "no-regression", ("bugs",), 0.3, 3)


def test_better_ships_only_on_a_better_primary_with_every_guard_passing() -> None:
    assert overall(verdicts(kept="BETTER", bugs="PASS"), BETTER_RULE, True) == "SHIP"
    assert (
        overall(verdicts(kept="BETTER", bugs="INCONCLUSIVE"), BETTER_RULE, True) == "INCONCLUSIVE"
    )
    assert overall(verdicts(kept="INCONCLUSIVE", bugs="PASS"), BETTER_RULE, True) == "INCONCLUSIVE"
    assert overall(verdicts(kept="BETTER", bugs="WORSE"), BETTER_RULE, True) == "HURT"


def test_worse_uses_the_alpha_the_caller_divides_among_ruled_metrics() -> None:
    old, new = units([1.0] * 5), units([0.0] * 5)  # p_worse = 1/32 = 0.031
    assert compare(GUARD, old, new, guard=True).verdict == "WORSE"
    assert compare(GUARD, old, new, guard=True, worse_alpha=0.05 / 3).verdict == "INCONCLUSIVE"


def test_no_regression_ships_only_when_every_ruled_metric_passes() -> None:
    assert overall(verdicts(kept="PASS", bugs="PASS"), SAFE_RULE, True) == "SHIP"
    assert overall(verdicts(kept="PASS", bugs="INCONCLUSIVE"), SAFE_RULE, True) == "INCONCLUSIVE"


def test_an_unruled_must_hold_failure_still_hurts() -> None:
    assert (
        overall(verdicts(kept="BETTER", bugs="PASS", no_exploit="WORSE"), BETTER_RULE, True)
        == "HURT"
    )


def test_missing_samples_are_inconclusive_but_still_report_harm() -> None:
    assert overall(verdicts(kept="BETTER", bugs="PASS"), BETTER_RULE, False) == "INCONCLUSIVE"
    assert overall(verdicts(kept="WORSE", bugs="PASS"), BETTER_RULE, False) == "HURT"


def test_detectable_effect_shrinks_with_more_units() -> None:
    small, large = detectable_effect(6, 3, runs=200), detectable_effect(20, 3, runs=200)
    assert large < small


def test_control_power_rises_with_units_the_target_changes() -> None:
    changed, unchanged = (0.0, 1.0), (0.0, 0.0)
    assert control_power([[changed]] * 8, 3, 0.05 / 3, runs=100) == 1.0
    assert control_power([[unchanged]] * 8, 3, 0.05 / 3, runs=100) == 0.0
    weak = control_power([[changed]] * 4 + [[unchanged]] * 4, 3, 0.05 / 3, runs=100)
    assert weak == 0.0  # four regressing units can never reach p < 0.0167


def test_control_power_pools_a_clusters_cases_as_a_screen_does() -> None:
    noisy = (0.3, 0.7)
    single = control_power([[noisy]] * 6, 3, 0.05 / 3, runs=200)
    paired = control_power([[noisy, noisy]] * 6, 3, 0.05 / 3, runs=200)
    assert paired > single


def test_judge_splits_alpha_among_the_ruled_metrics() -> None:
    old, new = {"bugs": units([1.0] * 5)}, {"bugs": units([0.0] * 5)}  # p_worse = 1/32
    two_guards = PassRule("kept", "better", ("bugs", "flags"), 0.3, 3)
    no_guards = PassRule("kept", "better", (), 0.3, 3)
    assert judge([GUARD], two_guards, old, new)["bugs"].verdict == "INCONCLUSIVE"
    assert judge([GUARD], no_guards, old, new)["bugs"].verdict == "WORSE"


def test_judge_holds_the_primary_to_non_inferiority_only_under_no_regression() -> None:
    kept = Metric("kept", "higher", margin=0.2)
    same = {"kept": units([1.0] * 8)}
    assert judge([kept], SAFE_RULE, same, same)["kept"].verdict == "PASS"
    assert judge([kept], BETTER_RULE, same, same)["kept"].verdict == "INCONCLUSIVE"


def test_a_watch_model_leaves_a_must_hold_failure_out_of_the_result() -> None:
    held = verdicts(kept="PASS", bugs="PASS", no_exploit="WORSE")
    assert overall(held, SAFE_RULE, True) == "HURT"
    assert overall(held, SAFE_RULE, True, watch=True) == "SHIP"
