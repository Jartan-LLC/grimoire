"""Compare two arms task by task with an exact one-sided paired permutation test.

The unit is a case, or a cluster of related cases (their mean). For each unit, d is
new's mean minus old's, signed so that positive is better. Under "no difference" each
d is as likely to have either sign, so the p-value is the share of the 2^m sign
assignments whose sum is at least (or at most) the observed one, counted exactly.
Small suites can show only large effects; tests/evals/README.md says what follows.
"""

import random
from collections.abc import Iterable
from dataclasses import dataclass

from .suite import Metric, PassRule

ALPHA = 0.05
POWER = 0.8
BASE_RATE = 0.5  # a 0/1 check's noisiest pass rate
ROUND = 9  # decimals kept when summing d values, so equal sums meet in one bucket
TIE = 1e-6  # sums this close count as equal: rounding at each step can split a tie


@dataclass(frozen=True)
class MetricVerdict:
    """One metric's comparison."""

    metric: str
    units: int
    old_mean: float
    new_mean: float
    gains: int
    regressions: int
    p_better: float
    p_worse: float
    verdict: str
    must_hold: bool = False
    new_samples: int = 0


def sign_flip_p(diffs: list[float]) -> tuple[float, float]:
    """Exact one-sided p-values (better, worse) for the sum of `diffs` under random signs.

    The distribution of the signed sum is built by convolution, one unit at a time,
    so it costs the number of distinct partial sums, not 2^m.
    """
    observed = round(sum(diffs), ROUND)
    counts: dict[float, int] = {0.0: 1}
    for d in diffs:
        step: dict[float, int] = {}
        for total, n in counts.items():
            for signed in (d, -d):
                key = round(total + signed, ROUND)
                step[key] = step.get(key, 0) + n
        counts = step
    whole = 2 ** len(diffs)
    at_least = sum(n for total, n in counts.items() if total >= observed - TIE)
    at_most = sum(n for total, n in counts.items() if total <= observed + TIE)
    return at_least / whole, at_most / whole


def unit_diffs(old: dict[str, list[float]], new: dict[str, list[float]]) -> list[float]:
    """New's mean minus old's per unit both arms scored: positive is better."""
    return [
        sum(new[u]) / len(new[u]) - sum(old[u]) / len(old[u])
        for u in sorted(old.keys() & new.keys())
        if old[u] and new[u]
    ]


def _mean(scores: dict[str, list[float]]) -> float:
    values = [sum(v) / len(v) for v in scores.values() if v]
    return sum(values) / len(values) if values else 0.0


def compare(
    metric: Metric,
    old: dict[str, list[float]],
    new: dict[str, list[float]],
    guard: bool,
    worse_alpha: float = ALPHA,
) -> MetricVerdict:
    """The metric's verdict from per-unit sample scores.

    WORSE when p_worse < `worse_alpha`: the caller divides ALPHA among the metrics the
    pass rule reads (Bonferroni), so that a change that does nothing comes out HURT on a
    relative test by chance in at most ALPHA of screens. Primary: BETTER when p_better < ALPHA. Guard:
    PASS when the harm is shown to be within the margin, that is when shifting every d
    up by the margin still leaves p_better < ALPHA (non-inferiority). A must-hold
    metric is WORSE on any new sample below 1. Anything else is INCONCLUSIVE.
    """
    diffs = unit_diffs(old, new)
    p_better, p_worse = sign_flip_p(diffs) if diffs else (1.0, 1.0)
    if (
        metric.must_hold and any(s < 1 for scores in new.values() for s in scores)
    ) or p_worse < worse_alpha:
        verdict = "WORSE"
    elif not guard:
        verdict = "BETTER" if p_better < ALPHA else "INCONCLUSIVE"
    elif diffs and sign_flip_p([d + metric.margin for d in diffs])[0] < ALPHA:
        verdict = "PASS"
    else:
        verdict = "INCONCLUSIVE"
    return MetricVerdict(
        metric=metric.id,
        units=len(diffs),
        old_mean=_mean(old),
        new_mean=_mean(new),
        gains=sum(d > 0 for d in diffs),
        regressions=sum(d < 0 for d in diffs),
        p_better=p_better,
        p_worse=p_worse,
        verdict=verdict,
        must_hold=metric.must_hold,
        new_samples=sum(len(scores) for scores in new.values()),
    )


def worse_alpha(rule: PassRule) -> float:
    """ALPHA divided among the metrics the pass rule reads, the primary and each guard."""
    return ALPHA / (1 + len(rule.guards))


def judge(
    metrics: Iterable[Metric],
    rule: PassRule,
    old: dict[str, dict[str, list[float]]],
    new: dict[str, dict[str, list[float]]],
) -> dict[str, MetricVerdict]:
    """Every metric's verdict from each arm's per-metric, per-unit scores.

    The guards, and under `no-regression` the primary, are tested for non-inferiority;
    every metric is WORSE at worse_alpha(rule).
    """
    return {
        m.id: compare(
            m, old.get(m.id, {}), new.get(m.id, {}),
            guard=m.id in rule.guards or (m.id == rule.primary and rule.rule == "no-regression"),
            worse_alpha=worse_alpha(rule),
        )
        for m in metrics
    }  # fmt: skip


def overall(
    verdicts: dict[str, MetricVerdict], rule: PassRule, complete: bool, watch: bool = False
) -> str:
    """SHIP, HURT or INCONCLUSIVE.

    HURT when a ruled or must-hold metric is WORSE, even with samples missing.
    Otherwise, with every sample in, SHIP needs every guard to PASS, and for `better`
    the primary to be BETTER, for `no-regression` the primary to PASS too: a gain that
    may hide harm on a guard is no ship. On a watch model a must-hold failure is a
    standing limit of the text, reported apart, not part of the result.
    """
    ruled = [verdicts[m] for m in (rule.primary, *rule.guards) if m in verdicts]
    held = [] if watch else [v for v in verdicts.values() if v.must_hold]
    if any(v.verdict == "WORSE" for v in [*ruled, *held]):
        return "HURT"
    if not complete or len(ruled) < len((rule.primary, *rule.guards)):
        return "INCONCLUSIVE"
    guards_pass = all(verdicts[g].verdict == "PASS" for g in rule.guards)
    wanted = "BETTER" if rule.rule == "better" else "PASS"
    return "SHIP" if guards_pass and verdicts[rule.primary].verdict == wanted else "INCONCLUSIVE"


def smallest_p(units: int) -> float:
    """The smallest one-sided p a suite of `units` untied units can reach: 1/2^m."""
    return 1 / 2**units


def detectable_effect(
    units: int, samples: int, harm: bool = False, worse_alpha: float = ALPHA, runs: int = 400
) -> float:
    """The smallest true change on a 0/1 check the rule catches 80% of the time, by simulation.

    A gain, called BETTER, or with `harm` a loss, called WORSE at `worse_alpha`. Each
    unit is independent with a baseline pass rate of 0.5, the noisiest case, so real
    suites, whose rates sit nearer 0 or 1, can do better. Old and new each get
    `samples` draws. Returns more than 1.0 when no change up to 1 reaches 80%. A fixed
    seed keeps the planner's output stable.
    """
    rng = random.Random(92)  # noqa: S311 -- a seeded simulation, not a secret
    metric = Metric("m", "higher")
    wanted = "WORSE" if harm else "BETTER"
    for step in range(1, 21):
        effect = step * 0.05
        rate = max(0.0, BASE_RATE - effect) if harm else min(1.0, BASE_RATE + effect)
        hits = 0
        for _ in range(runs):
            old = {
                str(u): [float(rng.random() < BASE_RATE) for _ in range(samples)]
                for u in range(units)
            }
            new = {
                str(u): [float(rng.random() < rate) for _ in range(samples)] for u in range(units)
            }
            verdict = compare(metric, old, new, guard=False, worse_alpha=worse_alpha).verdict
            hits += verdict == wanted
        if hits / runs >= POWER:
            return effect
    return 1.05


def control_power(
    units: list[list[tuple[float, float]]], samples: int, worse_alpha: float, runs: int = 400
) -> float:
    """The chance a positive control comes out WORSE, by simulation.

    Each unit lists its cases' (old's failure rate, the control's failure rate), from
    the recorded baselines; each arm draws `samples` per case and pools a unit's cases,
    as a screen does. A fixed seed keeps the planner's output stable.
    """
    rng = random.Random(92)  # noqa: S311 -- a seeded simulation, not a secret
    metric = Metric("m", "higher")
    hits = 0
    for _ in range(runs):
        old = {
            str(u): [float(rng.random() >= f) for f, _ in cases for _ in range(samples)]
            for u, cases in enumerate(units)
        }
        new = {
            str(u): [float(rng.random() >= f) for _, f in cases for _ in range(samples)]
            for u, cases in enumerate(units)
        }
        hits += compare(metric, old, new, guard=True, worse_alpha=worse_alpha).verdict == "WORSE"
    return hits / runs
