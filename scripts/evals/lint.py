"""Check what a script can check about a suite before any session runs (part of make verify).

tests/evals/README.md holds the rules; this enforces the mechanical ones: the prompt
uses none of the case's hint words, the facts a check needs are where the writer can
find them, every planted problem fails its `verify` command and passes once fixed, the
passing references pass every check and each failing reference fails one, each target
case records a baseline failure, no baseline was drawn under another runner or, for a
remote case, another REMOTE_RUNNER, nor while a case without a remote had one, and a `gh`
check reads a case whose session records its gh calls. It cannot tell that every check
can fail, only that some check fails on each failing reference.
"""

import fnmatch
import os
import pathlib
import shlex
import shutil
import subprocess
import tempfile

from .grade import reference_scores
from .proc import run
from .session import REMOTE_RUNNER, RUNNER, build_fixture, git_env
from .suite import Case, Suite, SuiteError, load_suite

VERIFY_TIMEOUT_S = 60


def _verify(case: Case, command: str, fixed: bool) -> int | None:
    """The exit code of a plant's `verify` command in the fixture as a session gets it, or None on a timeout.

    The fixture is built the way a session's is, `build.py` included, so a problem the
    build plants is verified too; `fix/` is then laid over it when `fixed`. The origin
    the runner makes for a remote case is not made here: `verify` sees an origin only when
    `build.py` makes one.
    """
    with tempfile.TemporaryDirectory(prefix="grimoire-lint-") as scratch:
        work = pathlib.Path(scratch) / "repo"
        build_fixture(case, work, git_env(dict(os.environ)))
        if fixed and (case.path / "fix").is_dir():
            shutil.copytree(case.path / "fix", work, dirs_exist_ok=True)
        try:
            done = run(
                shlex.split(command), cwd=work, env=git_env(dict(os.environ)),
                capture_output=True, timeout=VERIFY_TIMEOUT_S, check=False,
            )  # fmt: skip
        except subprocess.TimeoutExpired:
            return None
        return int(done.returncode)


def _fact_problems(case: Case) -> list[str]:
    found: list[str] = []
    for fact in case.facts:
        fixture_file = case.path / "fixture" / fact.where.removeprefix("fixture:")
        if fact.where == "prompt":
            text = case.prompt
        elif fact.where.startswith("fixture:") and fixture_file.is_file():
            text = fixture_file.read_text()
        else:
            found.append(
                f"{case.path}: fact {fact.text!r} names {fact.where!r}, not prompt or a fixture file"
            )
            continue
        if fact.text not in text:
            found.append(f"{case.path}: fact {fact.text!r} is not in {fact.where}")
    return found


def _plant_problems(case: Case) -> list[str]:
    found: list[str] = []
    for plant in case.plants:
        where = f"{case.path}: plant {plant.id!r}"
        if not (case.path / "fix").is_dir():
            found.append(f"{where} has no fix/ to show it can be fixed")
            continue
        if (code := _verify(case, plant.verify, fixed=False)) in (0, None):
            found.append(f"{where}: verify {'passes' if code == 0 else 'times out'} on the fixture")
        if (code := _verify(case, plant.verify, fixed=True)) != 0:
            found.append(f"{where}: verify fails with fix/ applied (exit {code})")
    return found


def _reference_problems(case: Case) -> list[str]:
    found: list[str] = []
    if any(c.artifact != "delivery" for c in case.checks):
        if not any(r.passes for r in case.references):
            found.append(f"{case.path}: no reference/pass*.toml")
        if case.kind == "target" and all(r.passes for r in case.references):
            found.append(f"{case.path}: no reference/fail*.toml for the target check")
    for reference in case.references:
        results = reference_scores(case, reference)
        if reference.passes and (failed := [c.metric for c, s in results if s < 1]):
            found.append(f"{case.path}: reference {reference.name} fails {', '.join(failed)}")
        if not reference.passes and results and all(s == 1 for _, s in results):
            found.append(f"{case.path}: reference {reference.name} passes every check")
    return found


def case_problems(case: Case) -> list[str]:
    """One message per rule the case breaks."""
    prompt = case.prompt.lower()
    found = [f"{case.path}: prompt.md gives away {h!r}" for h in case.hints if h.lower() in prompt]
    found += _fact_problems(case) + _plant_problems(case) + _reference_problems(case)
    if not case.remote and any(c.artifact == "gh" for c in case.checks):
        found.append(
            f"{case.path}: a gh check needs remote = true or a [[gh]] reply, "
            "or the session's gh calls are not recorded"
        )
    if case.kind == "target" and not any(b.failures for b in case.baselines):
        found.append(f"{case.path}: a target case needs a [[baseline]] that failed at least once")
    found += [
        f"{case.path}: the {b.model} {b.arm} baseline was drawn under runner {b.runner}, not {RUNNER}; redraw it"
        for b in case.baselines
        if b.runner != RUNNER
    ]
    found += [
        f"{case.path}: the {b.model} {b.arm} baseline was drawn under remote_runner "
        f"{b.remote_runner}, not {REMOTE_RUNNER}; redraw it"
        for b in case.baselines
        if case.remote and b.remote_runner != REMOTE_RUNNER
    ]
    found += [
        f"{case.path}: the {b.model} {b.arm} baseline was drawn under remote_runner "
        f"{b.remote_runner}, while the case had a remote; redraw it"
        for b in case.baselines
        if not case.remote and b.remote_runner
    ]
    return found


def suite_problems(suite: Suite, root: pathlib.Path, tracked: list[str]) -> list[str]:
    """One message per rule the suite or one of its cases breaks."""
    where = suite.path / "suite.toml"
    found = [
        f"{where}: covers {glob!r} matches no tracked file"
        for glob in suite.covers
        if not any(fnmatch.fnmatch(f, glob) for f in tracked)
    ]
    plugin, _, name = suite.target.partition(":")
    base = root / "plugins" / plugin
    if not any(
        p.is_file()
        for p in (
            base / "skills" / name / "SKILL.md",
            base / "agents" / f"{name}.md",
            base / "commands" / f"{name}.md",
        )
    ):
        found.append(f"{where}: target {suite.target!r} is no skill, agent or command")
    by_id = {c.id: c for c in suite.cases}
    for burned in suite.burned:
        if burned not in by_id:
            found.append(f"{where}: BURNED names {burned!r}, which is not a case")
        elif by_id[burned].split != "dev":
            found.append(f"{where}: burned case {burned!r} is still in {by_id[burned].split}")
    for case in suite.cases:
        found += case_problems(case)
    return found


def lint(root: pathlib.Path, tracked: list[str]) -> list[str]:
    """Every problem in every suite under tests/evals/."""
    found: list[str] = []
    for config in sorted((root / "tests" / "evals").glob("**/suite.toml")):
        try:
            suite = load_suite(config.parent)
        except SuiteError as error:
            found.append(str(error))
            continue
        found += suite_problems(suite, root, tracked)
    return found
