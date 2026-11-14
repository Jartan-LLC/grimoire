"""Check what a script can check about a suite before any session runs (part of make verify).

tests/evals/README.md holds the rules; this enforces the mechanical ones: the prompt and
the later turns use none of the case's hint words, a case's `without` names only
plugins, the facts a check needs are where the writer can find them, every planted
problem fails its `verify` command and passes once fixed, the passing references pass
every check and each failing reference fails one, each target case records a baseline
failure, no baseline was drawn under another RUNNER or, for a remote case, another
REMOTE_RUNNER, no baseline of a case without a remote records a remote_runner, a `gh`
check reads a case whose session records its gh calls, a judge's tracked stamp and
labels parse and the stamp still describes the judge (its version, labels and
references), and git ignores no file a suite's plan pin or sessions read, so the committed
suite is the one that ran. It cannot tell that every check can fail, only that some check
fails on each failing reference; judged checks are not run on references.
"""

import fnmatch
import os
import pathlib
import shutil
import tempfile
import tomllib

from . import calibrate, jury
from .grade import reference_scores
from .proc import GIT, run
from .session import REMOTE_RUNNER, RUNNER, build_fixture, git_env, verify
from .suite import (
    SESSION_ARTIFACTS,
    Case,
    Suite,
    SuiteError,
    load_suite,
    python_cache,
    target_files,
)


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
        return verify(command, work, git_env(dict(os.environ)))


def _fact_problems(case: Case) -> list[str]:
    found: list[str] = []
    for fact in case.facts:
        fixture_file = case.path / "fixture" / fact.where.removeprefix("fixture:")
        if fact.where == "prompt":
            text = "\n".join((case.prompt, *case.turns))
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
    if any(c.artifact not in SESSION_ARTIFACTS for c in case.checks):
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
    turns = "\n".join(case.turns).lower()
    found += [f"{case.path}: a turn gives away {h!r}" for h in case.hints if h.lower() in turns]
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


def suite_problems(
    suite: Suite, root: pathlib.Path, tracked: list[str], ignored: dict[str, str]
) -> list[str]:
    """One message per rule the suite or one of its cases breaks.

    `ignored` maps each file git ignores to the rule that ignores it, as `git_ignored` returns.
    """
    where = suite.path / "suite.toml"
    found = [
        f"{where}: covers {glob!r} matches no tracked file"
        for glob in suite.covers
        if not any(fnmatch.fnmatch(f, glob) for f in tracked)
    ]
    # The plan pin hashes every file under the suite but Python caches, so a file git
    # ignores there makes a clone's run differ from the one that ran here.
    found += [
        f"{path}: git ignores it ({rule}), so the committed suite lacks it; "
        "force-add it with git add -f or delete it"
        for name, rule in sorted(ignored.items())
        if (path := root / name).is_relative_to(suite.path) and not python_cache(path)
    ]
    plugin, _, name = suite.target.partition(":")
    base = root / "plugins" / plugin
    if not any((base / p).is_file() for p in target_files(name)):
        found.append(f"{where}: target {suite.target!r} is no skill, agent, command or hook script")
    by_id = {c.id: c for c in suite.cases}
    for burned in suite.burned:
        if burned not in by_id:
            found.append(f"{where}: BURNED names {burned!r}, which is not a case")
        elif by_id[burned].split != "dev":
            found.append(f"{where}: burned case {burned!r} is still in {by_id[burned].split}")
    for case in suite.cases:
        found += case_problems(case)
        found += [
            f"{case.path}: without names {name!r}, which is no plugin"
            for name in case.without
            if not (root / "plugins" / name / ".claude-plugin" / "plugin.json").is_file()
        ]
    return found + judge_problems(suite)


def judge_problems(suite: Suite) -> list[str]:
    """A judge's stamp or labels that do not parse, or a stamp that no longer describes the judge."""
    found: list[str] = []
    for judge in suite.judges.values():
        folder = calibrate.judge_dir(suite.path, judge.id)
        try:
            calibrate.all_labels(folder / "labels")
        except (tomllib.TOMLDecodeError, KeyError, TypeError) as error:
            found.append(f"{folder / 'labels'}: labels do not parse: {error}")
            continue
        standing = calibrate.standing(suite.path, suite.cases, judge, jury.instrument(judge))
        if standing.stale:
            found.append(
                f"{folder / 'stamp.toml'}: {standing.stale}: restore what changed, which "
                "is the only fix for a held-out case's reference; for new labels or a dev "
                "case's reference, stamp the same version again with judge-align --set "
                "held-out; for an edited judge, tune the new version on dev first "
                "(tests/evals/README.md, 'Calibrating a judge')"
            )
    return found


def git_ignored(root: pathlib.Path) -> dict[str, str]:
    """Each file under tests/evals/ that git ignores, with the rule that does, as `<source>:<line>:<pattern>`.

    A file force-added past its rule is tracked, so it is not listed.
    """
    listed = run(
        [GIT, "ls-files", "-z", "--others", "--ignored", "--exclude-standard", "--", "tests/evals"],
        cwd=root,
        capture_output=True,
        text=True,
        check=True,
    ).stdout
    if not listed:
        return {}
    fields = run(
        [GIT, "check-ignore", "-z", "--verbose", "--stdin"],
        cwd=root,
        input=listed,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.split("\0")
    # Four fields per file: the ignore file, the line in it, the pattern, the file.
    return {
        fields[i + 3]: f"{fields[i]}:{fields[i + 1]}:{fields[i + 2]}"
        for i in range(0, len(fields) - 1, 4)
    }


def lint(root: pathlib.Path, tracked: list[str], ignored: dict[str, str]) -> list[str]:
    """Every problem in every suite under tests/evals/.

    `tracked` is every file git tracks and `ignored` each file under tests/evals/ it
    ignores, with the rule, as `git_ignored` returns; both name files relative to `root`.
    """
    found: list[str] = []
    for config in sorted((root / "tests" / "evals").glob("**/suite.toml")):
        try:
            suite = load_suite(config.parent)
        except SuiteError as error:
            found.append(str(error))
            continue
        found += suite_problems(suite, root, tracked, ignored)
    return found
