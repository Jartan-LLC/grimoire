"""Deterministic graders: a regex over an artifact, or a skill's delivery state."""

import dataclasses
import re
from collections.abc import Sequence

from . import trace
from .cache import Sample
from .suite import REPORT, Case, Check, Reference


class Uncollected(Exception):  # noqa: N818 -- reads as the condition, like StopIteration
    """A check reads a file the sample was drawn without collecting."""


def text_of(
    commits: Sequence[str], final: str, files: dict[str, str], artifact: str,
    reports: dict[str, str] | None = None,
) -> str:  # fmt: skip
    """The text a check reads: every commit message, the final reply, one collected file, or an agent's reports."""
    if artifact == "commits":
        return "\n\n".join(commits)
    if artifact == "final":
        return final
    if artifact.startswith(REPORT):
        return (reports or {}).get(artifact.removeprefix(REPORT), "")
    return files.get(artifact.removeprefix("file:"), "")


def reports_of(parsed: trace.Trace) -> dict[str, str]:
    """Each agent's reports in the session, joined in the order they were handed back."""
    joined: dict[str, list[str]] = {}
    for report in parsed.reports:
        joined.setdefault(report.agent, []).append(report.text)
    return {agent: "\n\n".join(texts) for agent, texts in joined.items()}


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

    Only the deliveries and writes of `check.agent` count: the main thread's when it
    names none, otherwise that subagent's. With a write kind, every successful write
    of that kind must find the skill in that state, and no such write fails. Without
    one, the skill must have arrived at some point (`loaded`) or never (`not-loaded`).
    """
    skill = str(check.skill)
    deliveries = [d for d in parsed.deliveries if d.agent == check.agent]
    if check.write is None:
        loaded = any(d.skill == skill for d in deliveries)
        return 1.0 if loaded == (check.state == "loaded") else 0.0
    own = dataclasses.replace(
        parsed, deliveries=deliveries, writes=[w for w in parsed.writes if w.agent == check.agent]
    )
    writes = [w for w in own.writes if w.kind == check.write and w.ok]
    held = bool(writes) and all(trace.state(own, w, skill)[0] == check.state for w in writes)
    return 1.0 if held else 0.0


def _mean_by_metric(pairs: list[tuple[str, float]]) -> dict[str, float]:
    by_metric: dict[str, list[float]] = {}
    for metric, score in pairs:
        by_metric.setdefault(metric, []).append(score)
    return {metric: sum(values) / len(values) for metric, values in by_metric.items()}


def scores(case: Case, sample: Sample, parsed: trace.Trace) -> dict[str, float]:
    """Each metric the case checks, as the mean of its checks' scores.

    A sample the arm spoiled (a timeout, the budget cap, the turn cap) fails every check.
    A `file:` check on a path the sample did not collect, one a key fix added after the
    draw, cannot be graded from it: the sample would read as an empty file.
    """
    pairs: list[tuple[str, float]] = []
    reports = reports_of(parsed)
    for check in case.checks:
        path = check.artifact.removeprefix("file:")
        if check.artifact != path and sample.collected is not None and path not in sample.collected:
            raise Uncollected(
                f"sample {sample.key} did not collect {path}, which its key now reads: "
                "draw fresh samples (a new --trial for a screen; for a baseline run, delete the "
                "case's samples from the cache)"
            )
        if sample.spoiled:
            score = 0.0
        elif check.artifact == "delivery":
            score = delivery_score(check, parsed)
        else:
            score = text_score(
                check, text_of(sample.commits, sample.final, sample.files, check.artifact, reports)
            )
        pairs.append((check.metric, score))
    return _mean_by_metric(pairs)


def case_failed(scores: dict[str, float], guards: tuple[str, ...]) -> bool:
    """Whether a sample got the case's own behaviour wrong: a metric it checks, guards aside, below 1."""
    return any(score < 1 for metric, score in scores.items() if metric not in guards)


def reference_scores(case: Case, reference: Reference) -> list[tuple[Check, float]]:
    """Each text check's score on a reference; delivery checks need a session."""
    outputs = (reference.commits, reference.final, reference.files)
    return [
        (check, text_score(check, text_of(*outputs, check.artifact, reference.reports)))
        for check in case.checks
        if check.artifact != "delivery"
    ]
