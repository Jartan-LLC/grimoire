"""Deterministic graders: a regex over an artifact, or a skill's delivery state."""

import re
from collections.abc import Sequence

from . import trace
from .cache import Sample
from .suite import Case, Check, Reference


def text_of(commits: Sequence[str], final: str, files: dict[str, str], artifact: str) -> str:
    """The text a check reads: every commit message, the final reply, or one collected file."""
    if artifact == "commits":
        return "\n\n".join(commits)
    if artifact == "final":
        return final
    return files.get(artifact.removeprefix("file:"), "")


def text_score(check: Check, text: str) -> float:
    """1.0 when a text check holds.

    An `absent` check fails on empty text: an agent that produced nothing did not
    keep the thing out, it skipped the task.
    """
    if check.present is not None:
        return 1.0 if re.search(check.present, text, re.MULTILINE) else 0.0
    if not text.strip():
        return 0.0
    return 0.0 if re.search(str(check.absent), text, re.MULTILINE) else 1.0


def delivery_score(check: Check, parsed: trace.Trace) -> float:
    """1.0 when the skill stood as the check wants.

    With a write kind, every successful write of that kind must find the skill in
    that state, and a session with no such write fails. Without one, the skill
    must have reached the session at some point (`loaded`) or never (`not-loaded`).
    """
    skill = str(check.skill)
    if check.write is None:
        loaded = any(d.skill == skill for d in parsed.deliveries)
        return 1.0 if loaded == (check.state == "loaded") else 0.0
    writes = [w for w in parsed.writes if w.kind == check.write and w.ok]
    held = bool(writes) and all(trace.state(parsed, w, skill)[0] == check.state for w in writes)
    return 1.0 if held else 0.0


def _mean_by_metric(pairs: list[tuple[str, float]]) -> dict[str, float]:
    by_metric: dict[str, list[float]] = {}
    for metric, score in pairs:
        by_metric.setdefault(metric, []).append(score)
    return {metric: sum(values) / len(values) for metric, values in by_metric.items()}


def scores(case: Case, sample: Sample, parsed: trace.Trace) -> dict[str, float]:
    """Each metric the case checks, as the mean of its checks' scores.

    A sample the arm spoiled (a timeout, the budget cap, the turn cap) fails every check.
    """
    pairs: list[tuple[str, float]] = []
    for check in case.checks:
        if sample.spoiled:
            score = 0.0
        elif check.artifact == "delivery":
            score = delivery_score(check, parsed)
        else:
            score = text_score(
                check, text_of(sample.commits, sample.final, sample.files, check.artifact)
            )
        pairs.append((check.metric, score))
    return _mean_by_metric(pairs)


def case_failed(scores: dict[str, float], guards: tuple[str, ...]) -> bool:
    """Whether a sample got the case's own behaviour wrong: a metric it checks, guards aside, below 1."""
    return any(score < 1 for metric, score in scores.items() if metric not in guards)


def reference_scores(case: Case, reference: Reference) -> list[tuple[Check, float]]:
    """Each text check's score on a hand-written reference; delivery checks need a session."""
    return [
        (
            check,
            text_score(
                check, text_of(reference.commits, reference.final, reference.files, check.artifact)
            ),
        )
        for check in case.checks
        if check.artifact != "delivery"
    ]
