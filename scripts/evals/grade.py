"""Graders: a regex over an artifact, a skill's delivery state, how the subagents worked, or a judge's kept answers."""

import dataclasses
import math
import posixpath
import re
from collections.abc import Collection, Iterable, Mapping, Sequence
from typing import cast

from . import gh_stub, trace
from .cache import Sample
from .suite import BRIEF, FILES, REPORT, SESSION_ARTIFACTS, Case, Check, Reference, glob_match


class Uncollected(Exception):  # noqa: N818 -- reads as the condition, like StopIteration
    """A check reads a file or a verify result the sample was drawn without collecting."""


class Unjudged(Exception):  # noqa: N818 -- reads as the condition, like StopIteration
    """A judged check's panel is not complete for the sample: judge it first."""


def advisory_metric(check: Check) -> str:
    """Where a judged check scores while its judge gates nothing: a metric of its own, reported only."""
    return f"{check.metric}@{check.judge}"


def metric_of(check: Check, advisory: Collection[str]) -> str:
    """The metric a check scores into: its own, or `advisory_metric` when its judge is in `advisory`."""
    return advisory_metric(check) if check.judge in advisory else check.metric


@dataclasses.dataclass(frozen=True)
class Outputs:
    """What text checks read, from a session or a reference.

    `reports` and `briefs` map an agent to its joined texts; `gh` is the `gh_text` of the
    recorded calls, or a reference's `gh` without Claude Code's own call lines.
    """

    commits: Sequence[str] = ()
    final: str = ""
    files: dict[str, str] = dataclasses.field(default_factory=dict[str, str])
    reports: dict[str, str] = dataclasses.field(default_factory=dict[str, str])
    gh: str = ""
    briefs: dict[str, str] = dataclasses.field(default_factory=dict[str, str])


def text_of(outputs: Outputs, artifact: str) -> str:
    """The text a check reads: the commit messages, the final reply, collected files, the gh calls, or an agent's reports or briefs."""
    whole = {"commits": "\n\n".join(outputs.commits), "final": outputs.final, "gh": outputs.gh}
    if artifact in whole:
        return whole[artifact]
    if artifact.startswith(FILES):
        return files_text(outputs.files, artifact.removeprefix(FILES))
    if artifact.startswith(REPORT):
        return outputs.reports.get(artifact.removeprefix(REPORT), "")
    if artifact.startswith(BRIEF):
        return outputs.briefs.get(artifact.removeprefix(BRIEF), "")
    return outputs.files.get(artifact.removeprefix("file:"), "")


def files_text(files: Mapping[str, str], pattern: str) -> str:
    """Every file the glob matches, in path order, each after a `==> <path> <==` line."""
    return "\n".join(
        f"==> {path} <==\n{text}"
        for path, text in sorted(files.items())
        if glob_match(path, pattern)
    )


def gh_text(calls: Sequence[dict[str, object]]) -> str:
    """The agent's calls the sandbox's `gh` recorded, one `gh <call_line>` line each, then their texts.

    The calls Claude Code makes on its own (`_claude_codes_call`) are dropped first; with
    none left the text is empty. After the call lines and a blank line come every
    non-blank text an argument could pass (`gh_stub.candidates`, titles and `--jq`
    strings included), each call's stdin and the files it named, newlines kept, each
    text once.
    """
    texts: dict[str, None] = {}
    lines: list[str] = []
    for call in calls:  # the stub's own log entries: argv, stdin, files
        argv = cast("list[str]", call.get("argv", []))
        line = f"gh {gh_stub.call_line(argv)}"
        if _claude_codes_call(line):
            continue
        lines.append(line)
        files = cast("dict[str, str]", call.get("files", {}))
        named = [c for arg in argv for c in gh_stub.candidates(arg)]
        texts.update(
            dict.fromkeys(
                t for t in (*named, str(call.get("stdin", "")), *files.values()) if t.strip()
            )
        )
    return "\n\n".join(["\n".join(lines), *texts]) if lines else ""


def _claude_codes_call(line: str) -> bool:
    """Whether a `gh` text line is a call Claude Code makes on its own, not the agent.

    On 2.1.311 it runs `gh pr view --json url`, and `gh pr view <branch> --json url` naming
    the branch; in the samples no agent ran either, while agents pass PR numbers.
    """
    words = line.split(" ")
    if words[:3] != ["gh", "pr", "view"] or words[-2:] != ["--json", "url"]:
        return False
    branch = words[3:-2]
    return not branch or (
        len(branch) == 1 and not branch[0].startswith("-") and not branch[0].isdigit()
    )


def agents_gh(text: str) -> str:
    r"""A reference's `gh` text without the lines of the calls Claude Code makes on its own.

    Only the call lines, before the first blank line, are filtered: a body text that
    quotes such a call keeps it. With no call line left the text is empty, as in
    `gh_text`. It splits on newlines alone, as `call_line` escapes only those: a body's
    `\r` stays inside its call's line.
    """
    calls, blank, texts = text.partition("\n\n")
    kept = [line for line in calls.split("\n") if not _claude_codes_call(line)]
    return "\n".join(kept) + blank + texts if kept else ""


def _by_agent(pairs: Iterable[tuple[str, str]]) -> dict[str, str]:
    joined: dict[str, list[str]] = {}
    for agent, text in pairs:
        joined.setdefault(agent, []).append(text)
    return {agent: "\n\n".join(texts) for agent, texts in joined.items()}


def reports_of(parsed: trace.Trace) -> dict[str, str]:
    """Each agent's reports in the session, joined in the order they were handed back."""
    return _by_agent((r.agent, r.text) for r in parsed.reports)


def briefs_of(parsed: trace.Trace) -> dict[str, str]:
    """Every Agent-call prompt the main thread sent each agent type, joined in the order sent; a call that ended in error aside."""
    return _by_agent((b.agent, b.text) for b in parsed.briefs)


def text_score(check: Check, text: str) -> float:
    """1.0 when a text check holds.

    An `absent` check fails when the agent produced nothing: it did not keep the thing
    out, it skipped the task.
    """
    if check.present is not None:
        return 1.0 if re.search(check.present, text, re.MULTILINE) else 0.0
    if not text.strip():
        return 0.0
    return 0.0 if re.search(str(check.absent), text, re.MULTILINE) else 1.0


def check_score(check: Check, outputs: Outputs) -> float:
    """A text check's score on `outputs`."""
    return text_score(check, text_of(outputs, check.artifact))


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


def overlap_score(parsed: trace.Trace) -> float:
    """1.0 when no file was written by two spawns; the main thread's writes and failed ones do not count."""
    writers: dict[str, set[str]] = {}
    for w in parsed.writes:
        if w.kind == "file" and w.ok and w.spawn:
            writers.setdefault(posixpath.normpath(w.text), set()).add(w.spawn)
    return 0.0 if any(len(spawns) > 1 for spawns in writers.values()) else 1.0


def spawn_writes_score(check: Check, parsed: trace.Trace) -> float:
    """1.0 when no spawn, at any depth, made a write of `check.write`, even one that failed."""
    return 0.0 if any(w.kind == check.write and w.spawn for w in parsed.writes) else 1.0


def waves(parsed: trace.Trace) -> list[tuple[int, float]]:
    """Each stretch of events from a main-thread Agent call to the last report of every spawn out with it.

    A spawn that never reported stays out to the end of the session.
    """
    spans = sorted(
        (s.index, math.inf if s.reported is None else s.reported) for s in parsed.spawns if not s.by
    )
    merged: list[tuple[int, float]] = []
    for start, end in spans:
        if merged and start <= merged[-1][1]:
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def barrier_score(parsed: trace.Trace) -> float:
    """1.0 when the main thread wrote no file, or tried to, inside a wave."""
    inside = any(
        start < w.index < end
        for w in parsed.writes
        if w.kind == "file" and not w.spawn
        for start, end in waves(parsed)
    )
    return 0.0 if inside else 1.0


def session_score(check: Check, sample: Sample, parsed: trace.Trace) -> float:
    """A delivery, verify or spawn check's score on the session."""
    if check.artifact == "verify":
        return 1.0 if (sample.verified or {}).get(str(check.command)) == 0 else 0.0
    if check.artifact == "delivery":
        return delivery_score(check, parsed)
    if check.artifact == "overlap":
        return overlap_score(parsed)
    if check.artifact == "spawn-writes":
        return spawn_writes_score(check, parsed)
    return barrier_score(parsed)


def _mean_by_metric(pairs: list[tuple[str, float]]) -> dict[str, float]:
    by_metric: dict[str, list[float]] = {}
    for metric, score in pairs:
        by_metric.setdefault(metric, []).append(score)
    return {metric: sum(values) / len(values) for metric, values in by_metric.items()}


def outputs_of(sample: Sample, parsed: trace.Trace) -> Outputs:
    """What a sample's text checks read."""
    return Outputs(
        sample.commits, sample.final, sample.files,
        reports_of(parsed), gh_text(sample.gh or []), briefs_of(parsed),
    )  # fmt: skip


def judged_text(check: Check, sample: Sample, outputs: Outputs) -> str | None:
    """The text a judged check sends the judge, or None when it scores 0 without one.

    A spoiled sample and an empty artifact fail with no call, as an `absent` check fails
    on empty output.
    """
    text = text_of(outputs, check.artifact)
    return None if sample.spoiled or not text.strip() else text


def scores(  # noqa: PLR0913 -- `unjudged_ok` says what a missing judge answer does
    case: Case,
    sample: Sample,
    parsed: trace.Trace,
    judged: Mapping[int, float] | None = None,
    advisory: Collection[str] = (),
    *,
    unjudged_ok: bool = False,
) -> dict[str, float]:
    """Each metric the case checks, as the mean of its checks' scores.

    A sample the arm spoiled (a timeout, the budget cap, the turn cap) fails every check.
    A `file:` check on a path the sample did not collect, one a key fix added after the
    draw, cannot be graded from it: the sample would read as an empty file. A judged
    check reads its panel's score from `judged`, by the check's index in the key; a
    missing one raises Unjudged, or with `unjudged_ok` leaves its metric out of the result,
    so that no metric is scored on part of its checks. One whose judge is in `advisory`
    (no stamp shows it cleared its bar) scores into `advisory_metric` instead of its own,
    so it gates nothing.
    """
    pairs: list[tuple[str, float]] = []
    unjudged: set[str] = set()
    outputs = outputs_of(sample, parsed)
    for index, check in enumerate(case.checks):
        if (missing := _uncollected(check, sample)) is not None:
            raise Uncollected(
                f"sample {sample.key} did not collect {missing}, which its key now reads: "
                "draw fresh samples (a new --trial for a screen; for a baseline run, delete the "
                "case's samples from the store)"
            )
        metric = metric_of(check, advisory)
        if sample.spoiled:
            score = 0.0
        elif check.artifact in SESSION_ARTIFACTS:
            score = session_score(check, sample, parsed)
        elif check.judge is not None:
            found = _judged_score(check, index, sample, outputs, judged or {})
            if found is None and not unjudged_ok:
                raise Unjudged(
                    f"sample {sample.key}: judge {check.judge} has not answered check {index}"
                )
            if found is None:
                unjudged.add(metric)
                continue
            score = found
        else:
            score = check_score(check, outputs)
        pairs.append((metric, score))
    return {m: s for m, s in _mean_by_metric(pairs).items() if m not in unjudged}


def _uncollected(check: Check, sample: Sample) -> str | None:
    """What a check reads that the sample was drawn without, as a key fix after the draw would add."""
    if check.artifact == "verify":
        ran = sample.verified or {}
        return None if check.command in ran else f"the result of {check.command!r}"
    if check.artifact.startswith("file:"):
        wanted = check.artifact.removeprefix("file:")
    elif check.artifact.startswith(FILES):
        wanted = check.artifact
    else:
        return None
    return None if sample.collected is None or wanted in sample.collected else wanted


def _judged_score(
    check: Check, index: int, sample: Sample, outputs: Outputs, judged: Mapping[int, float]
) -> float | None:
    if judged_text(check, sample, outputs) is None:
        return 0.0
    return judged.get(index)


def case_failed(scores: dict[str, float], guards: tuple[str, ...]) -> bool:
    """Whether a sample got the case's own behaviour wrong: a metric it checks, guards aside, below 1."""
    return any(score < 1 for metric, score in scores.items() if metric not in guards)


def reference_outputs(reference: Reference) -> Outputs:
    """What a reference's text checks read."""
    return Outputs(
        reference.commits, reference.final, reference.files,
        reference.reports, agents_gh(reference.gh), reference.briefs,
    )  # fmt: skip


def reference_scores(case: Case, reference: Reference) -> list[tuple[Check, float]]:
    """Each regex check's score on a reference; delivery and spawn checks need a session, judged ones a judge."""
    outputs = reference_outputs(reference)
    return [
        (check, check_score(check, outputs))
        for check in case.checks
        if check.artifact not in SESSION_ARTIFACTS and check.judge is None
    ]
