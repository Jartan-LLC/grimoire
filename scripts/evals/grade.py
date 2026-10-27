"""Deterministic graders: a regex over an artifact, or a skill's delivery state."""

import dataclasses
import re
from collections.abc import Iterable, Sequence
from typing import cast

from . import gh_stub, trace
from .cache import Sample
from .suite import BRIEF, REPORT, Case, Check, Reference

# `-b` is `--body` only for these: `pr checkout -b` and `browse -b` name a branch.
SHORT_BODY = {("pr", c) for c in ("create", "edit", "comment", "review", "merge")} | {
    ("issue", c) for c in ("create", "edit", "comment")
}
# A release's body is its notes: `--notes`, or `-n`.
NOTES = {("release", "create"), ("release", "edit")}
# `api`'s fields; a `-F`/`--field` value `@path` is a file, which the stub reads.
API_FIELDS = ("-f", "--raw-field", "-F", "--field")


class Uncollected(Exception):  # noqa: N818 -- reads as the condition, like StopIteration
    """A check reads a file the sample was drawn without collecting."""


@dataclasses.dataclass(frozen=True)
class Outputs:
    """What text checks read, from a session or a reference.

    `reports` and `briefs` map an agent to its joined texts; `gh` is the `gh_text` of the
    recorded calls.
    """

    commits: Sequence[str] = ()
    final: str = ""
    files: dict[str, str] = dataclasses.field(default_factory=dict[str, str])
    reports: dict[str, str] = dataclasses.field(default_factory=dict[str, str])
    gh: str = ""
    briefs: dict[str, str] = dataclasses.field(default_factory=dict[str, str])


def text_of(outputs: Outputs, artifact: str) -> str:
    """The text a check reads: the commit messages, the final reply, a collected file, the gh calls, or an agent's reports or briefs."""
    if artifact == "commits":
        return "\n\n".join(outputs.commits)
    if artifact == "final":
        return outputs.final
    if artifact == "gh":
        return outputs.gh
    if artifact.startswith(REPORT):
        return outputs.reports.get(artifact.removeprefix(REPORT), "")
    if artifact.startswith(BRIEF):
        return outputs.briefs.get(artifact.removeprefix(BRIEF), "")
    return outputs.files.get(artifact.removeprefix("file:"), "")


def _command(argv: Sequence[str]) -> tuple[str, ...]:
    """The call's command and subcommand (`pr`, `create`), past any `-R`/`--repo` and flag."""
    words: list[str] = []
    after_repo = False
    for arg in argv:
        if after_repo or arg.startswith("-"):
            after_repo = arg in ("-R", "--repo")
            continue
        words.append(arg)
    return tuple(words[:2])


def _inline_bodies(argv: Sequence[str]) -> list[str]:
    """The bodies a call passes as arguments: `--body`, `-b` where it means that, a release's notes, `api`'s `body=`."""
    command = _command(argv)
    flags = ("--body", "-b") if command in SHORT_BODY else ("--body",)
    if command in NOTES:
        flags = ("--notes", "-n")
    found = [value for _, value in gh_stub.flag_values(argv, flags)]
    if command[:1] == ("api",):
        for flag, value in gh_stub.flag_values(argv, API_FIELDS):
            key, eq, text = value.partition("=")
            if key == "body" and eq and not (flag in gh_stub.FIELD_FLAGS and text.startswith("@")):
                found.append(text)
    return found


def gh_text(calls: Sequence[dict[str, object]]) -> str:
    """The calls the sandbox's `gh` recorded, one `gh <call_line>` line each, then their bodies.

    The bodies are each call's `--body`, `-b` where it means that, a release's `--notes` or
    `-n` and `api` `body=` field texts, then its stdin and body files, newlines kept.
    """
    lines: list[str] = []
    bodies: list[str] = []
    for call in calls:  # the stub's own log entries: argv, stdin, files
        argv = cast("list[str]", call.get("argv", []))
        files = cast("dict[str, str]", call.get("files", {}))
        lines.append(f"gh {gh_stub.call_line(argv)}")
        inline = _inline_bodies(argv)
        bodies += [t for t in (*inline, str(call.get("stdin", "")), *files.values()) if t.strip()]
    return "\n\n".join(["\n".join(lines), *bodies]) if calls else ""


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
    """The `gh` text without the lines of the calls Claude Code makes on its own."""
    return "\n".join(line for line in text.splitlines() if not _claude_codes_call(line))


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


def text_score(check: Check, text: str, produced: str | None = None) -> float:
    """1.0 when a text check holds.

    An `absent` check fails when the agent produced nothing: it did not keep the thing
    out, it skipped the task. `produced` is the agent's part of `text`, when not all of it.
    """
    if check.present is not None:
        return 1.0 if re.search(check.present, text, re.MULTILINE) else 0.0
    if not (text if produced is None else produced).strip():
        return 0.0
    return 0.0 if re.search(str(check.absent), text, re.MULTILINE) else 1.0


def check_score(check: Check, outputs: Outputs) -> float:
    """A text check's score on `outputs`; for `gh`, only the agent's calls count as produced."""
    text = text_of(outputs, check.artifact)
    return text_score(check, text, agents_gh(text) if check.artifact == "gh" else None)


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
    outputs = Outputs(
        sample.commits, sample.final, sample.files,
        reports_of(parsed), gh_text(sample.gh or []), briefs_of(parsed),
    )  # fmt: skip
    for check in case.checks:
        path = check.artifact.removeprefix("file:")
        if check.artifact != path and sample.collected is not None and path not in sample.collected:
            raise Uncollected(
                f"sample {sample.key} did not collect {path}, which its key now reads: "
                "draw fresh samples (a new --trial for a screen; for a baseline run, delete the "
                "case's samples from the store)"
            )
        if sample.spoiled:
            score = 0.0
        elif check.artifact == "delivery":
            score = delivery_score(check, parsed)
        else:
            score = check_score(check, outputs)
        pairs.append((check.metric, score))
    return _mean_by_metric(pairs)


def case_failed(scores: dict[str, float], guards: tuple[str, ...]) -> bool:
    """Whether a sample got the case's own behaviour wrong: a metric it checks, guards aside, below 1."""
    return any(score < 1 for metric, score in scores.items() if metric not in guards)


def reference_scores(case: Case, reference: Reference) -> list[tuple[Check, float]]:
    """Each text check's score on a reference; delivery checks need a session."""
    outputs = Outputs(
        reference.commits, reference.final, reference.files,
        reference.reports, reference.gh, reference.briefs,
    )  # fmt: skip
    return [
        (check, check_score(check, outputs))
        for check in case.checks
        if check.artifact != "delivery"
    ]
