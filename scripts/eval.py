#!/usr/bin/env python3
"""Run local skill evals. tests/evals/README.md says how to write and read them.

  plan                the suites the working tree's change needs, what no suite covers,
                      and per split the smallest effect each suite can see (free)
  lint                check every suite before any session runs (free; part of make verify)
  run SUITE --arm A   run SUITE's cases on arm none, old or new (spends inference)
  screen SUITE        run old and new side by side, then print the verdict (spends inference)
  show KEY            print one cached sample: its commits, final reply, deliveries and writes
  size SUITE          what each split can see per model, from the recorded baselines (free)

Sessions use the caller's own `claude` login; nothing here runs in CI. Samples are cached
(see scripts/evals/cache.py), so a rerun after a usage-limit stop resumes.
"""

import argparse
import dataclasses
import hashlib
import json
import pathlib
import random
import sys
from concurrent.futures import ThreadPoolExecutor
from typing import cast

from evals import cache, grade, session, trace
from evals.arms import Arm, merge_base, new_arm, none_arm, old_arm
from evals.lint import lint
from evals.plan import make_plan
from evals.proc import CLAUDE, GIT, run
from evals.suite import Case, Suite, SuiteError, load_suite, python_cache, tree_hash
from evals.verdict import (
    ALPHA,
    POWER,
    MetricVerdict,
    compare,
    control_power,
    detectable_effect,
    overall,
    smallest_p,
)

ROOT = pathlib.Path(__file__).resolve().parent.parent
READ_PASSING = 2  # passing samples per arm read at random, to catch passes for the wrong reason

type Scores = dict[str, dict[str, list[float]]]  # metric -> unit -> sample scores


def git(*args: str) -> str:
    """Output of a git command in this checkout."""
    return str(run([GIT, *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout)


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
    arms = store / "arms"
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
    breaker = session.Breaker()

    def one(item: Work) -> cache.Sample:
        case, arm, index, spec = item
        sample = session.run_sample(case, arm, index, spec, breaker)
        state = "ok" if sample.valid else "EXCLUDED " + "; ".join(sample.reasons)
        state += f" (spoiled: {sample.spoiled})" if sample.spoiled else ""
        print(f"  {arm.name} {case.id} #{index}: {state}", flush=True)
        return sample

    with ThreadPoolExecutor(max_workers=jobs) as pool:
        return list(pool.map(one, work))


def sample_scores(suite: Suite, sample: cache.Sample, store: pathlib.Path) -> dict[str, float]:
    """Each metric's score on one valid sample."""
    case = next(c for c in suite.cases if c.id == sample.case)
    parsed = trace.parse(trace.load_text(cache.read_events(store, sample.key)), sample.plugins)
    return grade.scores(case, sample, parsed)


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
    store: pathlib.Path,
    seed: str,
) -> list[str]:
    """The samples the practice says to read before trusting the result."""
    primary = suite.pass_rule.primary
    lines: list[str] = []
    for name, arm_samples in samples.items():
        valid = [s for s in arm_samples if s.valid]
        failing = [s for s in valid if sample_scores(suite, s, store).get(primary, 1.0) < 1]
        passing = [s for s in valid if s not in failing]
        lines += [f"- {name} {s.case} #{s.index} fails {primary}: {s.key}" for s in failing]
        picked = random.Random(seed + name).sample(  # noqa: S311 -- a reproducible pick, not a secret
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
    """What the plan fixes before the first run: a verdict is refused if any of it changes."""
    files = [p for p in suite.path.rglob("*") if p.is_file() and not python_cache(p)]
    return {
        "suite": tree_hash(suite.path, files),
        "split": split,
        "cases": sorted(c.id for c in suite.split(split)),
        "samples": samples,
        "model": spec.model,
        "claude_code": spec.version,
        "flags": session.claude_args("", old, spec.model, spec.budget_usd)[3:],
        "old": old.hash,
    }


def drawn(
    cases: list[Case], plan: dict[str, object], arms: dict[str, Arm], trial: str
) -> list[object]:
    """What a screen's sessions depend on: its samples' identity, without the grading.

    A fix to a key or a metric regrades the samples already drawn instead of drawing
    new ones; the plan pin still refuses a verdict until the change is acknowledged.
    """
    session_inputs = {k: v for k, v in plan.items() if k != "suite"}
    return [{c.id: c.hash() for c in cases}, session_inputs, arms["new"].hash, trial]


def check_plan(store: pathlib.Path, name: str, plan: dict[str, object], restart: bool) -> str:
    """'' when the plan matches the one fixed at this branch's first screen, else what changed.

    Plans are kept per branch, so one change's plan never binds another's.
    """
    branch = git("rev-parse", "--abbrev-ref", "HEAD").strip().replace("/", "--")
    path = store / "plans" / f"{name}--{branch}.json"
    if restart or not path.is_file():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(plan, indent=1))
        return ""
    fixed = json.loads(path.read_text())
    return ", ".join(k for k in plan if fixed.get(k) != plan[k])


def report(
    suite: Suite, verdicts: dict[str, MetricVerdict], result: str, refused: str, watch: bool
) -> list[str]:
    """The verdict block: a failed bar first, then the per-metric table.

    On a watch model the result is advisory: a relative WORSE is still reported, for the
    PR to explain, and a must-hold failure is reported as a standing limit of the text
    on that model rather than a failed bar.
    """
    lines: list[str] = []
    for v in verdicts.values():
        if v.verdict != "WORSE":
            continue
        detail = (
            f"{v.metric} WORSE -- new {v.new_mean:.3f} vs old {v.old_mean:.3f}, "
            f"{v.regressions} of {v.units} units regressed (p worse {v.p_worse:.3f})"
        )
        if not watch:
            lines.append(f"FAILED: {detail}")
        elif v.must_hold:
            lines.append(
                f"STANDING: {detail}; a limit of the text on this model, for its issue, not a bar"
            )
        else:
            lines.append(f"REPORT: {detail}; harm on a watch model, which the PR must explain")
    if refused:
        lines.append(
            f"NO VERDICT: the plan changed since the first screen ({refused}); --new-plan fixes a new one"
        )
        result = "HURT" if result == "HURT" else "INCONCLUSIVE"
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
    work = [
        (c, arms[a], i, specs[t])
        for t in trials
        for i in range(args.samples)
        for c in cases
        for a in ("old", "new")
    ]
    refused = check_plan(store, slug(suite, args.split), plan, args.new_plan)
    if refused:
        print(f"NO VERDICT: the plan changed since this branch's first screen ({refused}).")
        print(
            "Nothing was run. Fix a new plan with --new-plan (NEW_PLAN=1 with make) and say so in the PR."
        )
        return 1
    done = run_samples(work, args.jobs)
    for t in trials:
        trial_done = [
            sample for item, sample in zip(work, done, strict=True) if item[3] is specs[t]
        ]
        decide(Screen(args, suite, arms, plan, refused, store), t, trial_done)
    return 0


@dataclasses.dataclass(frozen=True)
class Screen:
    """What every trial of one screen shares."""

    args: argparse.Namespace
    suite: Suite
    arms: dict[str, Arm]
    plan: dict[str, object]
    refused: str
    store: pathlib.Path


def decide(run: Screen, trial: str, done: list[cache.Sample]) -> None:
    """Grade one trial's samples, print its result and write its evidence file."""
    args, suite, arms, plan, store = run.args, run.suite, run.arms, run.plan, run.store
    samples = {name: [s for s in done if s.arm == name] for name in arms}
    scores = {name: arm_scores(suite, s, store) for name, s in samples.items()}
    rule = suite.pass_rule
    verdicts = {
        m.id: compare(
            m, scores["old"].get(m.id, {}), scores["new"].get(m.id, {}),
            guard=m.id in rule.guards or (m.id == rule.primary and rule.rule == "no-regression"),
            worse_alpha=ALPHA / (1 + len(rule.guards)),
        )
        for m in suite.metrics.values()
    }  # fmt: skip
    complete = all(s.valid for s in done)
    lines = [f"== trial {trial}"] if trial else []
    watch = str(plan["model"]) in suite.watch
    lines += report(suite, verdicts, overall(verdicts, rule, complete), run.refused, watch)
    if not complete:
        lines.insert(
            0, "INCOMPLETE: some samples are still excluded after retries; rerun to retry them"
        )
    lines += ["", *(usage_line(n, s) for n, s in samples.items())]
    lines += ["", "Read before trusting the result (`python3 scripts/eval.py show KEY`):"]
    lines += to_read(suite, samples, scores, store, str(plan["suite"]) + trial)
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
    evidence = store / "evidence" / f"{slug(suite, args.split)}{suffix}.md"
    evidence.parent.mkdir(parents=True, exist_ok=True)
    evidence.write_text(text + "\n")
    print(f"\nevidence: {evidence}\n")


def split_report(suite: Suite) -> tuple[list[str], bool]:
    """What each held-out split can see, per model; and whether any split is too weak.

    Too weak: too few units for any verdict, or less than an 80% chance that a positive
    control (the target removed) comes out WORSE, estimated from the recorded baselines.
    A unit with no `none` baseline on a model counts as one the target does not change.
    """
    rule = suite.pass_rule
    worse_alpha = ALPHA / (1 + len(rule.guards))
    lines: list[str] = []
    weak = False
    for split in ("screen", "confirm"):
        cases = suite.split(split)
        units = sorted({suite.unit(c.id) for c in cases})
        if not units:
            lines.append(f"  {split}: no cases")
            weak = True
            continue
        harm = detectable_effect(len(units), rule.min_samples, harm=True, worse_alpha=worse_alpha)
        line = f"  {split}: {len(units)} units, smallest p {smallest_p(len(units)):.4f}; 80%-power harm on a 0/1 check: {_effect(harm)}"
        if rule.rule == "better":
            gain = detectable_effect(len(units), rule.min_samples)
            line += f", gain: {_effect(gain)}"
            if rule.min_effect and gain > rule.min_effect:
                line += f"; cannot see min_effect {rule.min_effect}"
                weak = True
        lines.append(line)
        if smallest_p(len(units)) >= worse_alpha:
            lines.append(f"  {split}: too few units for any verdict; add cases")
            weak = True
        for model in suite.models:
            rates = [_unit_rates([c for c in cases if suite.unit(c.id) == u], model) for u in units]
            power = control_power(rates, rule.min_samples, worse_alpha)
            needed = next(
                (
                    k
                    for k in range(rule.min_samples, 11)
                    if control_power(rates, k, worse_alpha) >= POWER
                ),
                None,
            )
            advice = (
                f"{needed} samples per case reach 80%"
                if needed
                else "no sample count up to 10 reaches 80%: add cases the target changes"
            )
            if model in suite.watch:
                advice += " (watch model: does not gate)"
            lines.append(
                f"    {model}: positive control comes out WORSE {power:.0%} of the time at {rule.min_samples} samples; {advice}"
            )
            weak = weak or (power < POWER and model not in suite.watch)
    return lines, weak


def _unit_rates(cases: list[Case], model: str) -> tuple[float, float]:
    """A unit's (old, none) failure rates on `model`: its cases' recorded means."""
    pairs: list[tuple[float, float]] = []
    for case in cases:
        old = case.failure_rate(model, "old") or 0.0
        none = case.failure_rate(model, "none")
        pairs.append((old, old if none is None else none))
    return sum(o for o, _ in pairs) / len(pairs), sum(n for _, n in pairs) / len(pairs)


def plan_command(base: str) -> int:
    """Print the suites the change needs, what no suite covers, and what each split can see."""
    plan = make_plan(ROOT, base)
    for error in plan.broken:
        print(f"BROKEN SUITE: {error}")
    weak = False
    for suite, hits in plan.suites:
        print(f"{shown(suite.path)}: covers {len(hits)} changed file(s)")
        lines, suite_weak = split_report(suite)
        print("\n".join(lines))
        weak = weak or suite_weak
        print(f"  next: make eval-screen SUITE={shown(suite.path)}")
    for path in plan.uncovered:
        print(
            f"UNCOVERED: {path} -- if the edit targets a behaviour you have seen go wrong, write cases first"
        )
    if not plan.suites and not plan.uncovered:
        print("no plugin behaviour changed: nothing to evaluate")
    return 1 if plan.broken or weak else 0


def _effect(effect: float) -> str:
    return f"{effect:.2f}" if effect <= 1 else "none up to 1.0"


def show(key: str, store: pathlib.Path) -> int:
    """Print one sample: its classification, commits, final reply, deliveries and writes."""
    sample = cache.load(store, key)
    if sample is None:
        raise SystemExit(f"no cached sample {key}")
    print(
        f"{sample.arm} {sample.case} #{sample.index} valid={sample.valid} spoiled={sample.spoiled or '-'} {sample.reasons}"
    )
    for message in sample.commits:
        print(f"\n--- commit\n{message}")
    print(f"\n--- final reply\n{sample.final}")
    parsed = trace.parse(trace.load_text(cache.read_events(store, key)), sample.plugins)
    print("\n--- skills delivered (event index)")
    for d in parsed.deliveries:
        print(f"  {d.index} {d.skill}")
    print("\n--- writes (event index)")
    for w in parsed.writes:
        print(f"  {w.index} {w.kind} ok={w.ok} {w.text[:120]!r}")
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
    delivery and the like), scores below 1. Recording replaces the case's
    [[baseline]] entry for this model and arm.
    """
    for case in cases:
        valid = [s for s in done if s.case == case.id and s.valid]
        failed = sum(
            grade.case_failed(sample_scores(suite, s, spec.store), suite.pass_rule.guards)
            for s in valid
        )
        print(f"  {case.id}: failed in {failed} of {len(valid)}")
        if args.record and valid:
            record_baseline(case.path / "key.toml", spec.model, args.arm, failed, len(valid))


def record_baseline(key: pathlib.Path, model: str, arm: str, failures: int, runs: int) -> None:
    """Replace the key's [[baseline]] entry for (model, arm) with these counts.

    Entries are written in one fixed form, at the end of the key, so a later record
    finds and replaces them.
    """
    entry = (
        f'[[baseline]]\nmodel = "{model}"\narm = "{arm}"\nfailures = {failures}\n'
        f"runs = {runs}\nrunner = {session.RUNNER}"
    )
    head = f'[[baseline]]\nmodel = "{model}"\narm = "{arm}"\n'
    blocks = key.read_text().rstrip("\n").split("\n\n")
    kept = [b for b in blocks if not b.startswith(head)]
    key.write_text("\n\n".join([*kept, entry]) + "\n")


def main() -> int:
    """Parse the command line and run one subcommand."""
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("plan").add_argument("--base", default="main")
    sub.add_parser("lint")
    sub.add_parser("show").add_argument("key")
    sub.add_parser("size").add_argument("suite")
    for name in ("run", "screen"):
        cmd = sub.add_parser(name)
        cmd.add_argument("suite")
        cmd.add_argument(
            "--split",
            default="screen" if name == "screen" else None,
            choices=("dev", "screen", "confirm"),
        )
        cmd.add_argument("--samples", type=int, default=3)
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
    args = parser.parse_args()
    store = cache.root()

    if args.command == "plan":
        return plan_command(args.base)
    if args.command == "lint":
        found = lint(ROOT, git("ls-files").split())
        print("\n".join(found) if found else "every eval suite passes its lint")
        return 1 if found else 0
    if args.command == "show":
        return show(args.key, store)
    if args.command == "size":
        suite = load(args.suite)
        lines, weak = split_report(suite)
        print(f"{shown(suite.path)}:")
        print("\n".join(lines))
        return 1 if weak else 0

    suite = load(args.suite)
    model = args.model or suite.models[0]
    if model not in suite.models:
        raise SystemExit(f"{model} is not one of the suite's models {list(suite.models)}")
    spec = session.Spec(model, claude_version(), suite.budget_usd, ROOT, store)
    if args.command == "screen":
        return screen(args, suite, spec, store)
    if args.arm == "new" and args.split is None:
        raise SystemExit(
            "run --arm new needs --split: new results on screen or confirm cases burn them"
        )
    arm = build_arm(args.arm, suite, args.base, args.new_ref, store)
    cases = [c for c in suite.split(args.split) if not args.cases or c.id in args.cases.split(",")]
    done = run_samples([(c, arm, i, spec) for i in range(args.samples) for c in cases], args.jobs)
    print(usage_line(arm.name, done))
    baseline_counts(suite, cases, done, spec, args)
    return 0


if __name__ == "__main__":
    sys.exit(main())
