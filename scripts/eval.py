#!/usr/bin/env python3
"""Run local skill evals. tests/evals/README.md says how to write and read them.

  plan [--tier N]     the suites the working tree's change reaches, each DIRECT or INDIRECT,
                      and what no suite covers; with a testing tier, the steps that tier
                      takes. It exits 1 when a suite fails to load, and at tier 4 when a
                      direct suite's split is too weak or a changed file has no suite (free)
  lint                check every suite before any session runs (free; part of make verify)
  run SUITE --arm A   run SUITE's cases on arm none, old or new (spends inference)
  screen SUITE        run old and new side by side, then print the verdict (spends inference)
  show KEY            print one stored sample: its commits, final reply, every gh call logged
                      and the gh text graded, deliveries and writes by agent, and subagents'
                      briefs and reports
  size SUITE          what each split can see per model, from the recorded baselines (free)
  judge-probe SUITE --judge ID       a few judge (and labeller) calls on stored samples,
                      printed raw, to check the flags and schema work (spends inference)
  judge-label SUITE --judge ID       silver-label the stored artifacts the judge reads, with
                      the labelling panel; --gold runs it on gold items (spends inference)
  judge-align SUITE --judge ID --set dev|held-out    score the judge against its labels and
                      gold items; on held-out, write its stamp (spends inference)

Sessions use the caller's own `claude` login; nothing here runs in CI. Samples are kept
(see scripts/evals/cache.py), so a rerun after a usage-limit stop resumes.
"""

import argparse
import dataclasses
import datetime
import functools
import hashlib
import json
import pathlib
import random
import sys
from collections.abc import Callable, Sequence
from concurrent.futures import ThreadPoolExecutor
from typing import cast

from evals import cache, calibrate, gh_stub, grade, jury, labeller, session, trace
from evals.arms import Arm, merge_base, new_arm, none_arm, old_arm
from evals.lint import lint
from evals.plan import Listed, first_gate, make_plan
from evals.proc import CLAUDE, GIT, run
from evals.suite import (
    EFFORTS,
    JUDGE_MODEL,
    Case,
    Check,
    Judge,
    Metric,
    Suite,
    SuiteError,
    load_suite,
    python_cache,
    tree_hash,
)
from evals.verdict import (
    POWER,
    MetricVerdict,
    control_power,
    detectable_effect,
    judge,
    overall,
    smallest_p,
    worse_alpha,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
READ_PASSING = 2  # passing samples per arm read at random, to catch passes for the wrong reason

type Scores = dict[str, dict[str, list[float]]]  # metric -> unit -> sample scores


def git(*args: str) -> str:
    """Output of a git command in this checkout."""
    return str(run([GIT, *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout)


def old_holds(target: str, base: str) -> bool:
    """Whether the merge base with `base` has `target`, so removing it is a real control."""
    plugin, _, name = target.partition(":")
    commit = merge_base(ROOT, base)
    paths = (f"skills/{name}/SKILL.md", f"agents/{name}.md", f"commands/{name}.md")
    return any(
        run(
            [GIT, "cat-file", "-e", f"{commit}:plugins/{plugin}/{p}"], cwd=ROOT, capture_output=True
        ).returncode
        == 0
        for p in paths
    )


def claude_version() -> str:
    """The installed Claude Code version, part of every sample's cache key."""
    return str(
        run([CLAUDE, "--version"], capture_output=True, text=True, check=True).stdout
    ).split()[0]


def shown(path: pathlib.Path) -> str:
    """`path` relative to the checkout when inside it."""
    return path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)


def slug(suite: Suite, split: str) -> str:
    """A file name for one suite and split."""
    return f"{shown(suite.path).strip('/').replace('/', '--')}--{split}"


def load(path: str) -> Suite:
    """The suite at `path`, or exit with its error."""
    try:
        return load_suite(pathlib.Path(path).resolve())
    except SuiteError as error:
        raise SystemExit(str(error)) from None


def build_arm(name: str, suite: Suite, base: str, new_ref: str | None, store: pathlib.Path) -> Arm:
    """Arm `old` (plugins at the merge base with `base`), `none` (old without the target) or `new`.

    `new` is the working tree, or `new_ref` when given: the merge base itself there is
    an A/A comparison, and `none` (old without the target) is the positive control.
    """
    arms = cache.arms(store)
    old = old_arm(ROOT, merge_base(ROOT, base), arms)
    if name == "old":
        return old
    if name == "none":
        return none_arm(old, suite.target, arms)
    if new_ref == "none":
        stripped = none_arm(old, suite.target, arms)
        return Arm("new", stripped.hash, stripped.plugins)
    if new_ref is not None:
        return old_arm(ROOT, new_ref, arms, name="new")
    return new_arm(ROOT, arms)


type Work = tuple[Case, Arm, int, session.Spec]


def run_samples(work: list[Work], jobs: int) -> list[cache.Sample]:
    """Every (case, arm, index, spec) sample, in order, running the missing ones `jobs` at a time."""
    session.preflight()
    breaker = session.Breaker()

    def one(item: Work) -> cache.Sample:
        case, arm, index, spec = item
        sample = session.run_sample(case, arm, index, spec, breaker)
        state = "ok" if sample.valid else "EXCLUDED " + "; ".join(sample.reasons)
        state += f" (spoiled: {sample.spoiled})" if sample.spoiled else ""
        print(f"  {arm.name} {case.id} #{index}: {state}: {sample.key}", flush=True)
        return sample

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        return list(pool.map(one, work))


def parsed_trace(store: pathlib.Path, sample: cache.Sample) -> trace.Trace:
    """The stored sample's trace, read with the skills its agents preloaded."""
    preloads = [(agent, skill) for agent, skill in sample.preloads or []]
    return trace.parse(
        trace.load_text(cache.read_events(store, sample.key)), sample.plugins, preloads
    )


def advisory(suite: Suite) -> dict[str, str]:
    """Each judge that may not gate, with why: its checks score as reported metrics only."""
    found: dict[str, str] = {}
    for j in suite.judges.values():
        why = calibrate.standing(suite.path, suite.cases, j, jury.instrument(j)).why_not
        if why:
            found[j.id] = why
    return found


def judged_texts(
    case: Case, sample: cache.Sample, parsed: trace.Trace
) -> dict[int, tuple[Check, str]]:
    """Each judged check of the case, by index, with the stripped text its judge reads.

    A check that scores 0 without a judge (a spoiled sample, an empty artifact) is left out.
    """
    outputs = grade.outputs_of(sample, parsed)
    found: dict[int, tuple[Check, str]] = {}
    for index, check in enumerate(case.checks):
        if check.judge is not None and (text := grade.judged_text(check, sample, outputs)):
            found[index] = (check, jury.strip(text, jury.names_of(ROOT)))
    return found


def panels(
    suite: Suite, sample: cache.Sample, store: pathlib.Path, parsed: trace.Trace | None = None
) -> dict[int, jury.Panel] | None:
    """The judge panels of a sample's judged checks, from kept answers; None while any is incomplete."""
    case = next(c for c in suite.cases if c.id == sample.case)
    if not any(c.judge for c in case.checks):
        return {}
    parsed = parsed or parsed_trace(store, sample)
    found: dict[int, jury.Panel] = {}
    for index, (check, text) in judged_texts(case, sample, parsed).items():
        panel = jury.lookup(store, suite.judges[str(check.judge)], check.reference, text)
        if panel is None:
            return None
        found[index] = panel
    return found


def fill_judgments(
    suite: Suite, samples: list[cache.Sample], store: pathlib.Path, jobs: int
) -> None:
    """Call the judges every valid sample still needs, printing each call that failed."""
    if not suite.judges:
        return
    work: list[jury.Job] = []
    for sample in samples:
        case = next(c for c in suite.cases if c.id == sample.case)
        if sample.valid and any(c.judge for c in case.checks):
            for check, text in judged_texts(case, sample, parsed_trace(store, sample)).values():
                work.append((suite.judges[str(check.judge)], check.reference, text))
    if work:
        failed = jury.fill(store, work, jobs)
        print(f"judged {len(work)} artifacts; {len(failed)} calls failed", flush=True)
        for line in failed:
            print(f"  {line}")


def sample_scores(suite: Suite, sample: cache.Sample, store: pathlib.Path) -> dict[str, float]:
    """Each metric's score on one valid sample; judged checks read kept judge answers."""
    case = next(c for c in suite.cases if c.id == sample.case)
    parsed = parsed_trace(store, sample)
    found = panels(suite, sample, store, parsed)
    if found is None:
        raise grade.Unjudged(f"sample {sample.key}: a judge panel is incomplete; rerun to judge it")
    by_check = {index: panel.score for index, panel in found.items()}
    return grade.scores(case, sample, parsed, by_check, advisory(suite) if suite.judges else {})


def judged(suite: Suite, sample: cache.Sample, store: pathlib.Path) -> bool:
    """Whether every judge panel the sample needs is complete; an excluded sample needs none."""
    return not suite.judges or not sample.valid or panels(suite, sample, store) is not None


def arm_scores(suite: Suite, samples: list[cache.Sample], store: pathlib.Path) -> Scores:
    """Metric -> unit -> every valid sample's score; a cluster's unit pools its cases' samples."""
    found: Scores = {}
    for sample in samples:
        if sample.valid:
            for metric, score in sample_scores(suite, sample, store).items():
                found.setdefault(metric, {}).setdefault(suite.unit(sample.case), []).append(score)
    return found


def usage_line(name: str, samples: list[cache.Sample]) -> str:
    """Mean tokens, cost, turns and tool calls per sample for one arm."""
    valid = [s for s in samples if s.valid]

    def mean(field: str) -> float:
        values: list[float] = []
        for s in valid:
            value = s.usage.get(field)
            if isinstance(value, dict):
                tokens = cast("dict[str, object]", value)
                value = sum(
                    v for k, v in tokens.items() if k.endswith("tokens") and isinstance(v, int)
                )
            values.append(float(value) if isinstance(value, (int, float)) else 0.0)
        return sum(values) / len(values) if values else 0.0

    excluded = sum(not s.valid for s in samples)
    spoiled = sum(bool(s.spoiled) for s in valid)
    return (
        f"- {name}: {len(valid)} samples ({excluded} excluded, {spoiled} spoiled); per sample "
        f"{mean('tokens'):,.0f} tokens, ${mean('cost_usd'):.2f}, {mean('turns'):.1f} turns, "
        f"{mean('tool_calls'):.1f} tool calls"
    )


def to_read(
    suite: Suite,
    samples: dict[str, list[cache.Sample]],
    scores: dict[str, Scores],
    verdicts: dict[str, MetricVerdict],
    store: pathlib.Path,
) -> list[str]:
    """The samples the practice says to read before trusting the result.

    Every failing sample of the primary metric, and of a metric that came out WORSE or
    must hold, so that the sample behind a HURT is always named.
    """
    primary = suite.pass_rule.primary
    named = [
        primary,
        *(m for m, v in verdicts.items() if m != primary and (v.must_hold or v.verdict == "WORSE")),
    ]
    lines: list[str] = []
    for name, arm_samples in samples.items():
        valid = [s for s in arm_samples if s.valid]
        failed = {
            s.key: [m for m in named if sample_scores(suite, s, store).get(m, 1.0) < 1]
            for s in valid
        }
        failing = [s for s in valid if failed[s.key]]
        passing = [s for s in valid if s not in failing]
        lines += [
            f"- {name} {s.case} #{s.index} fails {', '.join(failed[s.key])}"
            f"{f' (spoiled: {s.spoiled})' if s.spoiled else ''}: {s.key}"
            for s in failing
        ]
        seed = name + "".join(sorted(s.key for s in passing))  # the same samples, the same pick
        picked = random.Random(seed).sample(  # noqa: S311 -- a reproducible pick, not a secret
            passing, min(READ_PASSING, len(passing))
        )
        lines += [
            f"- {name} {s.case} #{s.index} passes (picked at random): {s.key}" for s in picked
        ]
    old, new = scores["old"].get(primary, {}), scores["new"].get(primary, {})
    for unit in sorted(old.keys() & new.keys()):
        if sum(new[unit]) / len(new[unit]) > sum(old[unit]) / len(old[unit]):
            lines.append(f"- unit {unit} counts as a gain: read its new samples")
        if not any(new[unit]) and not any(old[unit]):
            lines.append(f"- unit {unit} fails in both arms: check the case is not broken")
    return lines


def pinned(
    suite: Suite, split: str, samples: int, spec: session.Spec, old: Arm
) -> dict[str, object]:
    """What the plan fixes before the first run: a verdict is refused if any of it changes.

    The flags name the arm's plugin directories and the debug log by placeholder, so the
    plan, and with it the screen's samples, do not depend on where the store is.
    """
    files = [p for p in suite.path.rglob("*") if p.is_file() and not python_cache(p)]
    placed = dataclasses.replace(old, plugins={n: f"<arm>/plugins/{n}" for n in old.plugins})
    plan: dict[str, object] = {
        "suite": tree_hash(suite.path, files),
        "split": split,
        "cases": sorted(c.id for c in suite.split(split)),
        "samples": samples,
        "model": spec.model,
        "claude_code": spec.version,
        "flags": session.claude_args(
            "", placed, spec.model, spec.budget_usd, pathlib.Path("<sandbox>/debug.log")
        )[3:],
        "old": old.hash,
    }
    if suite.judges:  # absent otherwise, so a plan fixed before judges existed still matches
        plan["judges"] = {j.id: jury.instrument(j) for j in suite.judges.values()}
    return plan


def drawn(
    cases: list[Case], plan: dict[str, object], arms: dict[str, Arm], trial: str
) -> list[object]:
    """What a screen's sessions depend on: its samples' identity, without the grading.

    A fix to a key, a metric or a judge regrades the samples already drawn instead of
    drawing new ones; the plan pin still refuses a verdict until the change is acknowledged. A
    remote case's `[[gh]]` replies, though in its key, are part of its hash: editing
    them draws new samples.
    """
    session_inputs = {k: v for k, v in plan.items() if k not in ("suite", "judges")}
    return [{c.id: c.pinned() for c in cases}, session_inputs, arms["new"].hash, trial]


def check_plan(store: pathlib.Path, name: str, plan: dict[str, object], restart: bool) -> str:
    """'' when the plan matches the one fixed at this branch's first screen, else what changed.

    Plans are kept per branch and model, so one change's plan never binds another's,
    and a screen on one of the suite's models never refuses another's.
    """
    branch = git("rev-parse", "--abbrev-ref", "HEAD").strip().replace("/", "--")
    path = store / "plans" / f"{name}--{branch}.json"
    if restart or not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(plan, indent=1))
        return ""
    fixed = json.loads(path.read_text())
    return ", ".join(k for k in plan if fixed.get(k) != plan[k])


def report(suite: Suite, verdicts: dict[str, MetricVerdict], result: str, watch: bool) -> list[str]:
    """The verdict block: a failed bar first, then the per-metric table.

    On a watch model the result is advisory: a relative WORSE is still reported, for the
    PR to explain, and a must-hold failure is reported as a standing limit of the text
    on that model rather than a failed bar.
    """
    lines: list[str] = []
    rule = suite.pass_rule
    for v in verdicts.values():
        if v.verdict != "WORSE":
            continue
        detail = (
            f"{v.metric} WORSE -- new {v.new_mean:.3f} vs old {v.old_mean:.3f}, "
            f"{v.regressions} of {v.units} units regressed (p worse {v.p_worse:.3f})"
        )
        decides = v.must_hold or v.metric == rule.primary or v.metric in rule.guards
        if not decides:
            lines.append(f"REPORT: {detail}; a reported metric, which the PR must explain")
        elif not watch:
            lines.append(f"FAILED: {detail}")
        elif v.must_hold:
            lines.append(
                f"STANDING: {detail}; a limit of the text on this model, for its issue, not a bar"
            )
        else:
            lines.append(f"REPORT: {detail}; harm on a watch model, which the PR must explain")
    lines += [
        f"Result (watch model, advisory; gate models decide SHIP): {result}"
        if watch
        else f"Result: {result}",
        "",
        "| metric | role | units | old | new | gains | regressions | p better | p worse | verdict |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    rule = suite.pass_rule
    for v in verdicts.values():
        role = (
            "primary"
            if v.metric == rule.primary
            else "guard"
            if v.metric in rule.guards
            else "reported"
        )
        role += ", must hold" if v.must_hold else ""
        lines.append(
            f"| {v.metric} | {role} | {v.units} | {v.old_mean:.3f} | {v.new_mean:.3f} | {v.gains} "
            f"| {v.regressions} | {v.p_better:.3f} | {v.p_worse:.3f} | {v.verdict} |"
        )
    return lines


def screen(args: argparse.Namespace, suite: Suite, spec: session.Spec, store: pathlib.Path) -> int:
    """Run old and new interleaved on one split, for each trial, then grade and decide each.

    Several trials (A/A runs, say) share one pool of sessions, so they take the wall time
    of one screen at `jobs` sessions at a time, not one after another.
    """
    cases = suite.split(args.split)
    if not cases:
        raise SystemExit(f"no {args.split} cases in {shown(suite.path)}")
    arms = {name: build_arm(name, suite, args.base, args.new_ref, store) for name in ("old", "new")}
    plan = pinned(suite, args.split, args.samples, spec, arms["old"])
    trials = args.trial.split(",") if args.trial else [""]
    specs = {
        t: dataclasses.replace(
            spec,
            screen=hashlib.sha256(json.dumps(drawn(cases, plan, arms, t)).encode()).hexdigest()[
                :16
            ],
        )
        for t in trials
    }
    # Each pair's arms start together; which starts first alternates, so an effect of
    # start order cannot pass for one of the arms.
    work = [
        (c, arms[a], i, specs[t])
        for t in trials
        for i in range(args.samples)
        for n, c in enumerate(cases)
        for a in (("old", "new") if (n + i) % 2 == 0 else ("new", "old"))
    ]
    refused = check_plan(store, f"{slug(suite, args.split)}--{spec.model}", plan, args.new_plan)
    if refused:
        print(f"NO VERDICT: the plan changed since this branch's first screen ({refused}).")
        print(
            "Nothing was run. Fix a new plan with --new-plan (NEW_PLAN=1 with make) and say so in the PR."
        )
        return 1
    done = run_samples(work, args.jobs)
    fill_judgments(suite, done, store, args.jobs)
    for t in trials:
        trial_done = [
            sample for item, sample in zip(work, done, strict=True) if item[3] is specs[t]
        ]
        decide(Screen(args, suite, arms, plan, store), t, trial_done)
    return 0


@dataclasses.dataclass(frozen=True)
class Screen:
    """What every trial of one screen shares."""

    args: argparse.Namespace
    suite: Suite
    arms: dict[str, Arm]
    plan: dict[str, object]
    store: pathlib.Path


def decide(run: Screen, trial: str, done: list[cache.Sample]) -> None:
    """Grade one trial's samples, print its result and write its evidence file."""
    args, suite, arms, plan, store = run.args, run.suite, run.arms, run.plan, run.store
    unjudged = [s for s in done if not judged(suite, s, store)]
    graded = [s for s in done if s not in unjudged]
    samples = {name: [s for s in graded if s.arm == name] for name in arms}
    scores = {name: arm_scores(suite, s, store) for name, s in samples.items()}
    rule = suite.pass_rule
    verdicts = judge(judged_metrics(suite), rule, scores["old"], scores["new"])
    complete = all(s.valid for s in done) and not unjudged
    lines = [f"== trial {trial}"] if trial else []
    watch = str(plan["model"]) in suite.watch
    lines += report(suite, verdicts, overall(verdicts, rule, complete, watch), watch)
    if not complete:
        lines.insert(
            1 if trial else 0,
            "INCOMPLETE: some samples are still excluded after retries, or their judge panels "
            f"incomplete ({len(unjudged)}); rerun to retry them",
        )
    lines += judge_lines(suite, graded, store, str(plan["model"]))
    lines += ["", *(usage_line(n, s) for n, s in samples.items())]
    lines += ["", "Read before trusting the result (`python3 scripts/eval.py show KEY`):"]
    lines += to_read(suite, samples, scores, verdicts, store)
    lines += split_panels(suite, graded, store)
    new = args.new_ref or f"working tree at {git('rev-parse', '--short', 'HEAD').strip()}"
    lines += [
        "",
        f"- suite {shown(suite.path)}, split {args.split}: {len(suite.split(args.split))} cases x {args.samples} samples",
        f"- old {merge_base(ROOT, args.base)[:12]} (plugins {arms['old'].hash[:12]}); "
        f"new {new} (plugins {arms['new'].hash[:12]})",
        f"- model {plan['model']}, Claude Code {plan['claude_code']}, plan {str(plan['suite'])[:12]}",
    ]
    text = "\n".join(lines)
    print(text)
    suffix = f"--{trial}" if trial else ""
    evidence = store / "evidence" / f"{slug(suite, args.split)}--{plan['model']}{suffix}.md"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(text + "\n")
    print(f"\nevidence: {evidence}\n")


def judged_metrics(suite: Suite) -> list[Metric]:
    """The suite's metrics, then a reported metric for each judged check whose judge may not gate."""
    held = advisory(suite)
    extra = {
        grade.advisory_metric(c)
        for case in suite.cases
        for c in case.checks
        if c.judge is not None and c.judge in held
    }
    return [*suite.metrics.values(), *(Metric(m, "higher") for m in sorted(extra))]


def _artifact_models(check: Check, parsed: trace.Trace, session_model: str) -> set[str]:
    if check.artifact.startswith("report:"):
        return {
            r.model for r in parsed.reports if r.agent == check.artifact.removeprefix("report:")
        }
    return {session_model}


def judge_lines(
    suite: Suite, samples: list[cache.Sample], store: pathlib.Path, session_model: str
) -> list[str]:
    """What the screen says about its judges: which gate nothing and why, warnings from their stamps.

    A judge whose model wrote the artifact it judges is named: self-preference is a known
    judge bias, and calibration on another model's artifacts does not measure it.
    """
    if not suite.judges:
        return []
    lines = [""]
    held = advisory(suite)
    for judge_id, why in sorted(held.items()):
        lines.append(
            f"ADVISORY: judge {judge_id} gates nothing ({why}); its checks report as metric@{judge_id}"
        )
    for j in suite.judges.values():
        stamp = calibrate.standing(suite.path, suite.cases, j, jury.instrument(j)).stamp
        if stamp is not None and j.id not in held:
            lines += [
                f"WARNING: judge {j.id}: {r.name}: {r.value}"
                for r in calibrate.rows(stamp)
                if r.status == "warn"
            ]
    self_judged: set[str] = set()
    for sample in samples:
        case = next(c for c in suite.cases if c.id == sample.case)
        if sample.valid and any(c.judge for c in case.checks):
            parsed = parsed_trace(store, sample)
            self_judged |= {
                str(c.judge)
                for c in case.checks
                if c.judge is not None
                and suite.judges[c.judge].model in _artifact_models(c, parsed, session_model)
            }
    lines += [
        f"WARNING: judge {j} grades artifacts its own model wrote" for j in sorted(self_judged)
    ]
    return lines if len(lines) > 1 else []


def split_panels(suite: Suite, samples: list[cache.Sample], store: pathlib.Path) -> list[str]:
    """Each sample whose judge panel split on a check of the primary metric, to read; and the count per arm."""
    if not suite.judges:
        return []
    primary = suite.pass_rule.primary
    lines: list[str] = []
    per_arm: dict[str, int] = {}
    for sample in samples:
        case = next(c for c in suite.cases if c.id == sample.case)
        for index, panel in (panels(suite, sample, store) or {}).items() if sample.valid else ():
            if panel.split:
                per_arm[sample.arm] = per_arm.get(sample.arm, 0) + 1
                if case.checks[index].metric == primary:
                    votes = ", ".join(panel.votes)
                    lines.append(
                        f"- {sample.arm} {sample.case} #{sample.index} judge split ({votes}): {sample.key}"
                    )
    if per_arm:
        counts = ", ".join(f"{arm} {n}" for arm, n in sorted(per_arm.items()))
        lines.insert(0, f"- judge panels that split, per arm: {counts}")
    return lines


def split_report(
    suite: Suite,
    old_holds_target: bool = True,
    advise: bool = True,
    splits: tuple[str, ...] = ("screen", "confirm"),
) -> tuple[list[str], bool]:
    """What each of the held-out `splits` can see, per model; and whether any is too weak.

    Too weak: too few units for any verdict, or less than an 80% chance that a positive
    control (the target removed) comes out WORSE, estimated from the recorded baselines.
    A case missing either arm's baseline on a model counts as one the target does not change.
    The chance runs high: each case's few baseline runs are read as its exact failure rate,
    and baselines count each case's own non-guard checks, so a target case whose checks the
    pass rule does not read adds to it though the verdict cannot see that case. A target the merge base lacks
    gets no control at all, and a gate model missing either arm's baselines is too weak.
    With `advise`, a weak split's lines also say what fixes it: add cases, record baselines.
    """
    rule = suite.pass_rule
    alpha = worse_alpha(rule)
    lines: list[str] = []
    weak = False
    for split in splits:
        cases = suite.split(split)
        units = sorted({suite.unit(c.id) for c in cases})
        if not units:
            lines.append(f"  {split}: no cases")
            weak = True
            continue
        # Each metric the rule reads is tested only on the units whose cases check it.
        scored = min(
            len({suite.unit(c.id) for c in cases if any(k.metric == m for k in c.checks)})
            for m in (rule.primary, *rule.guards)
        )
        harm = detectable_effect(scored, rule.min_samples, harm=True, worse_alpha=alpha)
        line = f"  {split}: {len(units)} units, {scored} scored by every metric the rule reads, smallest p {smallest_p(scored):.4f}; 80%-power harm on a 0/1 check: {_effect(harm)}"
        if rule.rule == "better":
            gain = detectable_effect(scored, rule.min_samples)
            line += f", gain: {_effect(gain)}"
            if rule.min_effect and gain > rule.min_effect:
                line += f"; cannot see min_effect {rule.min_effect}"
                weak = True
        lines.append(line)
        lines += _judged_scale(suite, harm)
        if smallest_p(scored) >= alpha:
            lines.append(
                f"  {split}: too few units for any verdict" + ("; add cases" if advise else "")
            )
            weak = True
        for model in suite.models:
            if not old_holds_target:
                # Old lacks a new target, so the `none` control would be old against itself.
                lines.append(
                    f"    {model}: the target is not at the merge base yet: no positive control"
                )
                continue
            if not all(
                any(c.failure_rate(model, arm) is not None for c in cases)
                for arm in ("old", "none")
            ):
                lines.append(
                    f"    {model}: no old or no none baselines on this split"
                    + ("; record them" if advise else "")
                )
                weak = weak or model not in suite.watch
                continue
            rates = [[_case_rates(c, model) for c in cases if suite.unit(c.id) == u] for u in units]
            power = control_power(rates, rule.min_samples, alpha)
            needed = next(
                (k for k in range(rule.min_samples, 11) if control_power(rates, k, alpha) >= POWER),
                None,
            )
            advice = (
                f"{needed} samples per case reach 80%"
                if needed
                else "no sample count up to 10 reaches 80%"
                + (": add cases the target changes" if advise else "")
            )
            if model in suite.watch:
                advice += " (watch model: does not gate)"
            lines.append(
                f"    {model}: positive control comes out WORSE {power:.0%} of the time at {rule.min_samples} samples (optimistic); {advice}"
            )
            weak = weak or (power < POWER and model not in suite.watch)
    return lines, weak


def _judged_scale(suite: Suite, harm: float) -> list[str]:
    """For a primary metric a gating judge scores, its J and the harm on the true scale.

    Judge error shrinks every true effect by J = TPR + TNR - 1, so the harm the split
    sees, on the scale the judge observes, is a larger true harm.
    """
    primary = suite.pass_rule.primary
    held = advisory(suite)
    lines: list[str] = []
    for j in suite.judges.values():
        asked = any(
            c.judge == j.id and c.metric == primary for case in suite.cases for c in case.checks
        )
        stamp = calibrate.standing(suite.path, suite.cases, j, jury.instrument(j)).stamp
        if not asked or j.id in held or stamp is None or not (score := calibrate.j_of(stamp)):
            continue
        true = f"{harm / score:.2f}" if harm <= 1 else "none"
        lines.append(
            f"    judge {j.id} scores {primary}: J = {score:.2f}; that harm is {true} on the true scale"
        )
    return lines


def _case_rates(case: Case, model: str) -> tuple[float, float]:
    """A case's recorded (old, none) failure rates on `model`; one arm missing counts as unchanged."""
    old, none = case.failure_rate(model, "old"), case.failure_rate(model, "none")
    if old is None or none is None:
        same = old if old is not None else none or 0.0
        return same, same
    return old, none


# Which screens each testing tier runs lives here and in plan_command alone; "When a change
# needs evals" in tests/evals/README.md defines the tiers, the smoke test and when a change goes
# ahead.
SMOKE, FULL = 3, 4  # the tiers that write a smoke test and a full suite
UNCOVERED_STEP = {
    2: "name it in the PR as covered by no suite",
    SMOKE: "cover it in the smoke test",
    FULL: "write or extend a suite to cover it",
}


def next_steps(entry: Listed, path: str, tier: int) -> list[str]:
    """The steps tier `tier` (2 to 4) takes on one suite.

    A direct suite is screened on every model, and at tier 4 first gains cases the changed text
    affects (and confirm cases, if it has none) and is confirmed. An indirect one is screened
    once, from tier 3, on its first gate model, or its first model when all are watch models.
    """
    suite = entry.suite
    if not entry.direct and tier < SMOKE:
        return ["  nothing to run"]
    models = suite.models if entry.direct else (first_gate(suite),)
    lines: list[str] = []
    if entry.direct and tier == FULL:
        lines.append(
            '  first: add cases the changed text affects ("Choosing cases" in tests/evals/README.md)'
        )
        if not suite.split("confirm"):
            lines.append('  first: write confirm cases ("Splits" in tests/evals/README.md)')
    lines += [
        f"  next: make eval-screen SUITE={path} MODEL={model}"
        + (" (watch model: advisory)" if model in suite.watch else "")
        for model in models
    ]
    if entry.direct:
        if tier == FULL:
            lines.append("  then, before the PR: each of those again with SPLIT=confirm")
    elif models[0] in suite.watch:
        lines.append("  indirect: screen only, on its first model (all are watch models: advisory)")
    else:
        lines.append("  indirect: screen only, on one gate model")
    return lines


def plan_command(base: str, tier: int | None = None) -> int:
    """Print the suites the change reaches and what no suite covers; with `tier`, that tier's steps.

    Without a tier, the plan only lists what the change reaches and asks for one; at tier 1 it
    lists it with no steps, so a wrong tier-1 call shows what it waves through. It exits 1 when
    a suite does not load, and at tier 4, where a weak split binds, when a direct suite's split
    is too weak or a changed file has no suite; at tiers 2 and 3 the screen split's power report
    is printed for the PR to say what it shows, without its advice.
    """
    plan = make_plan(ROOT, base)
    for error in plan.broken:
        print(f"BROKEN SUITE: {error}")
    failed = bool(plan.broken)
    if not plan.suites and not plan.uncovered:
        print("no plugin behaviour changed: nothing to evaluate")
        return int(failed)
    for entry in plan.suites:
        suite = entry.suite
        kind = "DIRECT" if entry.direct else "INDIRECT"
        print(f"{shown(suite.path)}: {kind}, covers {', '.join(entry.hits)}")
        if tier is None or tier == 1:
            continue
        if entry.direct:
            binds = tier == FULL
            # The confirm split runs only at tier 4.
            splits = ("screen", "confirm") if binds else ("screen",)
            lines, weak = split_report(suite, old_holds(suite.target, base), binds, splits)
            print(
                "  what its splits can see:"
                if binds
                else "  what its screen split can see (say in the PR what it shows):"
            )
            print("\n".join(lines))
            failed = failed or (weak and binds)
        print("\n".join(next_steps(entry, shown(suite.path), tier)))
    failed = failed or (tier == FULL and bool(plan.uncovered))
    if tier == SMOKE:
        print('smoke test: write one ("Smoke tests" in tests/evals/README.md)')
    for path in plan.uncovered:
        print(
            f"UNCOVERED: {path}" + (f" -- {UNCOVERED_STEP[tier]}" if tier in UNCOVERED_STEP else "")
        )
    if tier == 1:
        print("no eval is due if nothing this change alters reaches the model")
    if tier is None:
        print(
            'pick the change\'s testing tier ("When a change needs evals" in tests/evals/README.md),'
            " then run make eval-plan TIER=<n>"
        )
    return int(failed)


def _effect(effect: float) -> str:
    return f"{effect:.2f}" if effect <= 1 else "none up to 1.0"


def show(key: str, store: pathlib.Path) -> int:
    """Print one sample: commits, final reply, graded files, gh calls and gh text, deliveries, writes, briefs, reports, hooks.

    The gh calls are every call the stub logged, Claude Code's own included; the gh text
    is what a check reads (`grade.gh_text`), without them.
    """
    sample = cache.load(store, key)
    if sample is None:
        raise SystemExit(f"no stored sample {key}")
    print(
        f"{sample.arm} {sample.case} #{sample.index} valid={sample.valid} spoiled={sample.spoiled or '-'} {sample.reasons}"
    )
    for message in sample.commits:
        print(f"\n--- commit\n{message}")
    print(f"\n--- final reply\n{sample.final}")
    for path, text in sorted(sample.files.items()):
        print(f"\n--- file {path}\n{text}")
    if sample.gh is not None:
        argvs = [cast("list[str]", call.get("argv", [])) for call in sample.gh]
        logged = "\n".join(f"gh {gh_stub.call_line(argv)}" for argv in argvs)
        print(f"\n--- gh calls: every call the stub logged, Claude Code's own included\n{logged}")
        print(f"\n--- gh text graded: Claude Code's own calls left out\n{grade.gh_text(sample.gh)}")
    parsed = parsed_trace(store, sample)
    print("\n--- skills delivered (event index, agent)")
    for d in parsed.deliveries:
        print(f"  {d.index} {d.skill} {d.agent or 'main'}")
    print("\n--- writes (event index, agent)")
    for w in parsed.writes:
        print(f"  {w.index} {w.kind} ok={w.ok} {w.agent or 'main'} {w.text[:120]!r}")
    for b in parsed.briefs:
        print(f"\n--- brief to {b.agent} (event index {b.index})\n{b.text}")
    for r in parsed.reports:
        print(f"\n--- report of {r.agent} on {r.model} (event index {r.index})\n{r.text}")
    print("\n--- hook context (event index)")
    for index, context in parsed.hook_contexts:
        print(f"  {index} {context[:120]!r}")
    return 0


def baseline_counts(
    suite: Suite,
    cases: list[Case],
    done: list[cache.Sample],
    spec: session.Spec,
    args: argparse.Namespace,
) -> None:
    """Print how often each case failed its own behaviour, and with `record` write it to its key.

    A sample fails when any metric the case checks, other than the guards (format,
    delivery and the like) and the reported metrics of judges that may not gate, scores
    below 1. Recording replaces the case's
    [[baseline]] entry for this model and arm, and only when every sample was drawn: a
    count cut short by a usage limit would be recorded as if it were whole.
    """
    for case in cases:
        drawn_here = [s for s in done if s.case == case.id]
        valid = [s for s in drawn_here if s.valid and judged(suite, s, spec.store)]
        failed = sum(
            grade.case_failed(
                {
                    m: v
                    for m, v in sample_scores(suite, s, spec.store).items()
                    if m in suite.metrics
                },
                suite.pass_rule.guards,
            )
            for s in valid
        )
        print(f"  {case.id}: failed in {failed} of {len(valid)}")
        if args.record and len(valid) < len(drawn_here):
            print(
                f"  {case.id}: not recorded, {len(drawn_here) - len(valid)} sample(s) excluded "
                "or not judged; rerun"
            )
        elif args.record and valid:
            record_baseline(
                case.path / "key.toml", spec.model, args.arm, failed, len(valid), remote=case.remote
            )


def record_baseline(  # noqa: PLR0913 -- `remote` adds a line to the entry the others make
    key: pathlib.Path, model: str, arm: str, failures: int, runs: int, *, remote: bool = False
) -> None:
    """Replace the key's [[baseline]] entry for (model, arm) with these counts.

    Entries are written in one fixed form, at the end of the key, so a later record
    finds and replaces them. A `remote` case's entry records REMOTE_RUNNER too.
    """
    entry = (
        f'[[baseline]]\nmodel = "{model}"\narm = "{arm}"\nfailures = {failures}\n'
        f"runs = {runs}\nrunner = {session.RUNNER}"
    ) + (f"\nremote_runner = {session.REMOTE_RUNNER}" if remote else "")
    head = f'[[baseline]]\nmodel = "{model}"\narm = "{arm}"\n'
    blocks = key.read_text().rstrip("\n").split("\n\n")
    kept = [b for b in blocks if not b.startswith(head)]
    key.write_text("\n\n".join([*kept, entry]) + "\n")


def _parser() -> argparse.ArgumentParser:
    """The command line: one subcommand per make target."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    plan = sub.add_parser("plan")
    plan.add_argument("--base", default="main")
    plan.add_argument(
        "--tier",
        type=int,
        choices=(1, 2, 3, 4),
        default=None,
        help='the change\'s testing tier ("When a change needs evals" in tests/evals/README.md)',
    )
    sub.add_parser("lint")
    sub.add_parser("show").add_argument("key")
    size = sub.add_parser("size")
    size.add_argument("suite")
    size.add_argument("--base", default="main")
    _judge_parsers(sub.add_parser)
    for name in ("run", "screen"):
        cmd = sub.add_parser(name)
        cmd.add_argument("suite")
        cmd.add_argument(
            "--split",
            default="screen" if name == "screen" else None,
            choices=("dev", "screen", "confirm"),
        )
        cmd.add_argument(
            "--samples", type=int, default=None, help="per case and arm (default: min_samples)"
        )
        cmd.add_argument("--base", default="main")
        cmd.add_argument("--model", default=None)
        cmd.add_argument("--jobs", type=int, default=12, help="sessions at a time")
        cmd.add_argument(
            "--new-ref",
            default=None,
            help="take new from this ref, or none (old without the target), instead of the working tree",
        )
        if name == "run":
            cmd.add_argument("--arm", required=True, choices=("none", "old", "new"))
            cmd.add_argument(
                "--cases", default=None, help="comma-separated case ids: run only these"
            )
            cmd.add_argument(
                "--record", action="store_true", help="write each case's baseline into its key"
            )
        else:
            cmd.add_argument(
                "--new-plan", action="store_true", help="fix a new plan, replacing the first"
            )
            cmd.add_argument(
                "--trial",
                default="",
                help="comma-separated names: screen once per name, all in one pool (A/A runs)",
            )
    return parser


@dataclasses.dataclass(frozen=True)
class Real:
    """A stored sample's artifact that a judge reads: the raw text and the model that wrote it."""

    sample: cache.Sample
    case: Case
    check: Check
    text: str
    model: str


MISSES = 10  # indices in a row with no stored sample that end the search for more


def drawn_samples(store: pathlib.Path, key: Callable[[int], str]) -> list[cache.Sample]:
    """The stored samples at `key(0)`, `key(1)` and on, until MISSES indices in a row hold none.

    A gap (a sample a usage-limit stop never ran) does not end the search early.
    """
    found: list[cache.Sample] = []
    index, missed = 0, 0
    while missed < MISSES:
        sample = cache.load(store, key(index))
        missed = 0 if sample is not None else missed + 1
        found += [sample] if sample is not None else []
        index += 1
    return found


def real_items(
    suite: Suite, judge_: Judge, specs: list[tuple[Arm, session.Spec]], store: pathlib.Path
) -> list[Real]:
    """Every valid, unspoiled baseline sample of a case that asks the judge whose artifact is not empty.

    Samples are found by the key each (case, arm, model) has now, as `run` draws them:
    one drawn on an older fixture, arm, runner, model or Claude Code is never picked up.
    """
    found: list[Real] = []
    for case in suite.cases:
        check = next((c for c in case.checks if c.judge == judge_.id), None)
        if check is None:
            continue
        for arm, spec in specs:
            for sample in drawn_samples(
                store, functools.partial(session.key_of, case, arm, spec=spec)
            ):
                if sample.valid and not sample.spoiled:
                    found += _real(store, sample, case, check)
    return found


def _real(store: pathlib.Path, sample: cache.Sample, case: Case, check: Check) -> list[Real]:
    """The sample as a real item, or nothing when its artifact is empty."""
    parsed = parsed_trace(store, sample)
    text = grade.text_of(grade.outputs_of(sample, parsed), check.artifact)
    if not text.strip():
        return []
    agent = check.artifact.removeprefix("report:")
    model = next((r.model for r in parsed.reports if r.agent == agent), "")
    return [Real(sample, case, check, text, model)]


def baseline_specs(
    args: argparse.Namespace, suite: Suite, store: pathlib.Path
) -> list[tuple[Arm, session.Spec]]:
    """Each arm of `--arms` against `--base`, on each of the suite's models, as `run` draws them."""
    names = args.arms.split(",")
    if stray := [n for n in names if n not in ("old", "none")]:
        raise SystemExit(f"--arms takes old and none, not {', '.join(stray)}")
    version = claude_version()
    return [
        (
            build_arm(name, suite, args.base, None, store),
            session.Spec(model, version, suite.budget_usd, ROOT, store, timeout_s=suite.timeout_s),
        )
        for name in names
        for model in suite.models
    ]


def _stripped(text: str) -> str:
    return jury.strip(text, jury.names_of(ROOT))


def _labelled(  # noqa: PLR0913 -- the call's inputs, and whether it may call
    store: pathlib.Path,
    panel: labeller.Labeller,
    case: Case,
    judge_: Judge,
    item: tuple[str, str],
    *,
    index: int,
    others: tuple[str, ...] = (),
    call: bool = True,
) -> labeller.Labelled | None:
    """One labeller's output on (reference, stripped text), kept or, with `call`, called; None without one."""
    key = labeller.key(panel, case.pinned(), judge_, item, index=index, others=others)
    if (kept := labeller.load(store, key)) is not None or not call:
        return kept
    reference, text = item
    out, raw = labeller.call(
        case,
        panel,
        lambda diff: labeller.prompt(
            case.prompt, diff, judge_.question, reference, text, others=others
        ),
    )
    if out is None:
        print(f"  labeller call failed ({case.id}): {raw.strip()[:200]}", flush=True)
        return None
    labeller.save(store, key, raw)
    return out


def panel_label(  # noqa: PLR0913 -- the call's inputs, and whether it may call
    store: pathlib.Path,
    panel: labeller.Labeller,
    case: Case,
    judge_: Judge,
    item: tuple[str, str],
    *,
    call: bool = True,
) -> tuple[tuple[str, ...], str] | None:
    """The labelling panel on one item: the three labellers' labels and the final one; None if one is missing."""
    _, text = item
    accepted = labeller.ratings(case, judge_)
    outs = [
        _labelled(store, panel, case, judge_, item, index=i, call=call)
        for i in range(labeller.LABELLERS)
    ]
    if any(o is None for o in outs):
        return None
    done = [o for o in outs if o is not None]
    votes = tuple(labeller.label_of(o, text, accepted) for o in done)
    if (final := labeller.unanimous(votes)) is not None:
        return votes, final
    others = tuple(json.dumps(dataclasses.asdict(o)) for o in done)
    adjudicated = _labelled(
        store, panel, case, judge_, item, index=labeller.LABELLERS, others=others, call=call
    )
    if adjudicated is None:
        return None
    return votes, labeller.label_of(adjudicated, text, accepted)


def sources(suite: Suite, judge_: Judge) -> calibrate.Sources:
    """The tracked material a judge's calibration items are made from."""
    folder = calibrate.judge_dir(suite.path, judge_.id)
    labels = calibrate.all_labels(folder / "labels")
    references = calibrate.judged_references(suite.cases, judge_.id)
    gold: dict[str, list[tuple[str, str, bool]]] = {}
    compare: dict[str, bool] = {}
    for case in suite.cases:
        check = next((c for c in case.checks if c.judge == judge_.id), None)
        if check is None:
            continue
        for ref in case.references:
            truth = calibrate.reference_truth(case, ref, judge_.compare)
            if truth is not None:
                text = calibrate.reference_text(check, ref)
                gold.setdefault(case.id, []).append((ref.name, text, truth))
        if judge_.compare:
            regex = [
                c
                for c in case.checks
                if c.metric == judge_.compare and c.judge is None and c.artifact == check.artifact
            ]
            for label in (lb for lb in labels if lb.case == case.id and regex):
                compare[label.id] = all(grade.text_score(c, label.text) == 1 for c in regex)
    return calibrate.Sources(references, gold, labels, compare)


def gold_panel(
    suite: Suite, judge_: Judge, panel: labeller.Labeller, store: pathlib.Path, *, call: bool
) -> tuple[int, int, list[str]]:
    """The labelling panel on the gold references and sibling swaps of both sets: right, out of, and the wrong ids.

    Without `call` only kept outputs count, and an item with none is left out.
    """
    by_id = {c.id: c for c in suite.cases}
    found = [
        item
        for which in ("dev", "held-out")
        for item in calibrate.items(judge_, which, sources(suite, judge_))
        if item.kind in ("reference", "sibling")
    ]
    right, n, wrong = 0, 0, list[str]()
    for item in found:
        pair = (item.reference, _stripped(item.text))
        result = panel_label(store, panel, by_id[item.case], judge_, pair, call=call)
        if result is None:
            continue
        n += 1
        if (result[1] == "yes") == item.truth and result[1] != "unsure":
            right += 1
        else:
            wrong.append(item.id)
    return right, n, wrong


def spread[T: Real](reals: Sequence[T], count: int) -> list[T]:
    """`count` items taken a case at a time, round robin in the order given, so a probe sees many cases."""
    by_case: dict[str, list[T]] = {}
    for real in reals:
        by_case.setdefault(real.case.id, []).append(real)
    rounds = max((len(v) for v in by_case.values()), default=0)
    ordered = [v[i] for i in range(rounds) for v in by_case.values() if i < len(v)]
    return ordered[:count]


def _judge_of(suite: Suite, judge_id: str) -> Judge:
    if judge_id not in suite.judges:
        raise SystemExit(f"{shown(suite.path)} has no [[judge]] {judge_id!r}")
    return suite.judges[judge_id]


def probe(args: argparse.Namespace, suite: Suite, judge_: Judge, store: pathlib.Path) -> int:
    """A few judge and labeller calls on stored samples, printed raw; nothing is kept."""
    reals = real_items(suite, judge_, baseline_specs(args, suite, store), store)
    if not reals:
        raise SystemExit("no stored sample of a case that asks this judge: draw some with run")
    for real in spread(reals, args.calls):
        text = _stripped(real.text)
        answer, raw = jury.call(judge_, real.check.reference, text)
        counted = jury.vote(answer, text) if answer else "-"
        print(
            f"\n== judge on {real.sample.key} ({real.case.id}): parsed {answer}, counted {counted}"
        )
        print(raw.strip()[:3000])
    panel = labeller.Labeller(args.labeller_model, args.labeller_effort)
    for real in spread(reals, args.labellers):
        text = _stripped(real.text)
        out, raw = labeller.call(
            real.case,
            panel,
            lambda diff, r=real, t=text: labeller.prompt(
                r.case.prompt, diff, judge_.question, r.check.reference, t
            ),
        )
        label = labeller.label_of(out, text, labeller.ratings(real.case, judge_)) if out else "-"
        print(f"\n== labeller on {real.sample.key} ({real.case.id}): label {label}")
        print(raw.strip()[:3000])
    return 0


def label(args: argparse.Namespace, suite: Suite, judge_: Judge, store: pathlib.Path) -> int:
    """Silver-label every stored artifact the judge reads that has no label yet; or, with --gold, gate the panel.

    New labels are appended to their case's file; a label once written is never changed.
    """
    panel = labeller.Labeller(args.labeller_model, args.labeller_effort)
    if args.gold:
        right, n, wrong = gold_panel(suite, judge_, panel, store, call=True)
        print(f"labelling panel on gold items: {right} of {n} right")
        print("\n".join(f"  wrong: {w}" for w in wrong))
        return 0 if n and right >= calibrate.LABELLER_GOLD * n else 1
    folder = calibrate.judge_dir(suite.path, judge_.id) / "labels"
    kept = calibrate.all_labels(folder)
    have = {lb.id for lb in kept}
    todo = [
        r
        for r in real_items(suite, judge_, baseline_specs(args, suite, store), store)
        if r.sample.key not in have
    ]
    print(f"{len(todo)} artifacts to label, {len(have)} labelled before", flush=True)

    def one(real: Real) -> calibrate.Label | None:
        result = panel_label(
            store, panel, real.case, judge_, (real.check.reference, _stripped(real.text))
        )
        if result is None:
            return None
        votes, final = result
        who = f"{panel.model} {panel.effort}"
        return calibrate.Label(
            real.sample.key, real.case.id, real.sample.arm, real.model, who, votes, final, real.text
        )

    with ThreadPoolExecutor(max_workers=args.jobs) as pool:
        new = [lb for lb in pool.map(one, todo) if lb is not None]
    for case_id in sorted({lb.case for lb in new}):
        path = folder / f"{case_id}.toml"
        before = calibrate.read_labels(path) if path.is_file() else []
        calibrate.write_labels(path, [*before, *(lb for lb in new if lb.case == case_id)])
    every = calibrate.all_labels(folder)
    fleiss, unsure = calibrate.agreement(every)
    print(f"labelled {len(new)} of {len(todo)}; {len(todo) - len(new)} left for a rerun")
    print(f"labellers' Fleiss kappa {fleiss}, unsure {unsure} of {len(every)}")
    stamp = calibrate.read_stamp(folder.parent / "stamp.toml")
    burned = stamp.burned if stamp else ()
    for which in ("dev", "held-out"):
        held = which == "held-out"
        in_set = [lb for lb in every if calibrate.in_held_out(judge_, lb, burned) == held]
        yes, no = (sum(lb.label == v for lb in in_set) for v in ("yes", "no"))
        print(f"  {which}: {yes} yes, {no} no (each needs {calibrate.MIN_CLASS})")
    return 0


def align(args: argparse.Namespace, suite: Suite, judge_: Judge, store: pathlib.Path) -> int:
    """Score the judge on one set's items; on held-out, once per judge version, write its stamp."""
    folder = calibrate.judge_dir(suite.path, judge_.id)
    old = calibrate.read_stamp(folder / "stamp.toml")
    instrument = jury.instrument(judge_)
    held = args.set == "held-out"
    tried = old.versions if old else ()
    if held and instrument in tried:
        raise SystemExit("this version of the judge was scored on held-out already: tune on dev")
    if held and len(tried) >= calibrate.MAX_VERSIONS:
        raise SystemExit(
            f"{len(tried)} versions were scored on held-out: report the missed bar (README, Judges)"
        )
    material = sources(suite, judge_)
    burned = old.burned if old else ()
    found = calibrate.items(judge_, args.set, material, burned)
    failed = jury.fill(store, [(judge_, i.reference, _stripped(i.text)) for i in found], args.jobs)
    print("\n".join(failed))
    panels_ = {i.id: jury.lookup(store, judge_, i.reference, _stripped(i.text)) for i in found}
    if missing := [k for k, p in panels_.items() if p is None]:
        print(f"INCOMPLETE: {len(missing)} items lack a full panel; rerun to retry them")
        return 1
    done = {k: p for k, p in panels_.items() if p is not None}
    verdicts = {k: p.score == 1 for k, p in done.items()}
    single = {k: p.votes[0] == "yes" for k, p in done.items()}
    natural = [i for i in found if i.kind == "natural"]
    every = material.labels
    fleiss, unsure = calibrate.agreement(every)
    panel_model = sorted({lb.labeller for lb in every})
    right, n, _ = gold_panel(suite, judge_, _panel_of(args, every), store, call=False)
    stamp = calibrate.Stamp(
        judge=judge_.id,
        instrument=instrument,
        versions=(*tried, instrument) if held else tried,
        labels=calibrate.labels_hash(folder / "labels"),
        labeller=", ".join(panel_model),
        date=datetime.datetime.now(datetime.UTC).date().isoformat(),
        cells=tuple(calibrate.cells(found, verdicts, single)),
        references={c: calibrate.text_hash(r) for c, r in material.references.items()},
        burned=burned,
        human_audited=old.human_audited if old else 0,
        gold_right=right,
        gold_n=n,
        labelled=len(every),
        unsure=unsure,
        fleiss=fleiss,
        unanimous=sum(not done[i.id].split for i in natural),
        panels=len(natural),
    )
    for row in calibrate.rows(stamp):
        print(f"{row.status:5} {row.name}: {row.value}")
    for item in found:  # an invariance item disagrees with its pair's answer
        truth = verdicts.get(item.pair) if item.pair else item.truth
        if truth is not None and verdicts[item.id] != truth:
            votes = ", ".join(done[item.id].votes)
            print(
                f"  disagrees: {item.kind} {item.case} {item.arm or '-'} {truth} ({votes}): {item.id}"
            )
    if not held:
        return 0
    passed = calibrate.cleared(stamp)
    if not passed:
        stamp = dataclasses.replace(stamp, burned=(*burned, *(i.id for i in natural)))
    calibrate.write_stamp(folder / "stamp.toml", stamp)
    print(f"{'CLEARED' if passed else 'MISSED'}: stamp written to {shown(folder / 'stamp.toml')}")
    return 0 if passed else 1


def _panel_of(args: argparse.Namespace, labels: Sequence[calibrate.Label]) -> labeller.Labeller:
    """The labelling panel the labels were written with, when they name one, else the command line's."""
    if len(names := {lb.labeller for lb in labels}) == 1:
        model, _, effort = next(iter(names)).partition(" ")
        return labeller.Labeller(model, effort)
    return labeller.Labeller(args.labeller_model, args.labeller_effort)


def _judge_parsers(add: Callable[[str], argparse.ArgumentParser]) -> None:
    """Add the judge-* subcommands with `add`, the subparsers' add_parser."""
    for name in ("judge-probe", "judge-label", "judge-align"):
        cmd = add(name)
        cmd.add_argument("suite")
        cmd.add_argument("--judge", required=True, help="the [[judge]] id")
        cmd.add_argument("--jobs", type=int, default=8, help="calls at a time")
        cmd.add_argument("--arms", default="old,none", help="stored samples of these arms")
        cmd.add_argument("--base", default="main", help="the arms' merge base, as for run")
        cmd.add_argument("--labeller-model", default=JUDGE_MODEL)
        cmd.add_argument("--labeller-effort", default="xhigh", choices=EFFORTS)
        if name == "judge-probe":
            cmd.add_argument("--calls", type=int, default=5, help="judge calls")
            cmd.add_argument("--labellers", type=int, default=2, help="labeller calls")
        if name == "judge-label":
            cmd.add_argument("--gold", action="store_true", help="label the gold items instead")
        if name == "judge-align":
            cmd.add_argument("--set", required=True, choices=("dev", "held-out"))


def judge_command(args: argparse.Namespace) -> int:
    """Run one judge-* subcommand."""
    suite = load(args.suite)
    judge_ = _judge_of(suite, args.judge)
    store = cache.root(ROOT)
    if args.command == "judge-probe":
        return probe(args, suite, judge_, store)
    if args.command == "judge-label":
        return label(args, suite, judge_, store)
    return align(args, suite, judge_, store)


def main() -> int:
    """Parse the command line and run one subcommand."""
    args = _parser().parse_args()

    if args.command == "plan":
        return plan_command(args.base, args.tier)
    if args.command == "lint":
        found = lint(ROOT, git("ls-files").split())
        print("\n".join(found) if found else "every eval suite passes its lint")
        return 1 if found else 0
    if args.command in ("show", "judge-probe", "judge-label", "judge-align"):
        return show(args.key, cache.root(ROOT)) if args.command == "show" else judge_command(args)
    if args.command == "size":
        suite = load(args.suite)
        lines, weak = split_report(suite, old_holds(suite.target, args.base))
        print(f"{shown(suite.path)}:")
        print("\n".join(lines))
        return 1 if weak else 0

    suite = load(args.suite)
    args.samples = args.samples or suite.pass_rule.min_samples
    model = args.model or suite.models[0]
    if model not in suite.models:
        raise SystemExit(f"{model} is not one of the suite's models {list(suite.models)}")
    store = cache.root(ROOT)
    spec = session.Spec(
        model, claude_version(), suite.budget_usd, ROOT, store, timeout_s=suite.timeout_s
    )
    if args.command == "screen":
        return screen(args, suite, spec, store)
    if args.arm == "new" and args.split is None:
        raise SystemExit(
            "run --arm new needs --split: new results on screen or confirm cases burn them"
        )
    if args.record and args.arm == "new":
        raise SystemExit("--record writes baselines for none and old only")
    arm = build_arm(args.arm, suite, args.base, args.new_ref, store)
    cases = [c for c in suite.split(args.split) if not args.cases or c.id in args.cases.split(",")]
    done = run_samples([(c, arm, i, spec) for i in range(args.samples) for c in cases], args.jobs)
    fill_judgments(suite, done, store, args.jobs)
    print(usage_line(arm.name, done))
    baseline_counts(suite, cases, done, spec, args)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (grade.Uncollected, grade.Unjudged) as error:
        sys.exit(f"cannot grade: {error}")
