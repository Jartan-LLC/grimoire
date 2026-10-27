"""Map a change to the suites that test it, following loads to the files that pull a changed skill in.

A changed skill also changes every agent that preloads it and every skill, agent,
command or hook that tells the agent to load it, so those are covered too, and so
on until nothing new is reached. The pointers come from `scripts/check-wiring.py`,
so the planner and `make verify` read the wiring alike. A suite that covers a changed
file is direct; one reached only through a file that loads a changed skill, agent or
command is indirect.
"""

import fnmatch
import importlib.util
import pathlib
from collections.abc import Callable
from dataclasses import dataclass

from .proc import GIT, run
from .suite import Suite, SuiteError, load_suite

# Changes no eval measures: release bookkeeping, user-facing docs, and the Codex files
# generated from sources the planner already maps (the runner drives Claude Code only).
UNTESTED = ("CHANGELOG.md", ".claude-plugin/plugin.json", ".codex-plugin/plugin.json", "README.md")
GENERATED = "/codex/"  # plugins/<plugin>/codex/...
SKILL_DEPTH = 4  # plugins/<plugin>/skills/<skill>/...
FILE_DEPTH = 4  # plugins/<plugin>/agents/<agent>.md


@dataclass(frozen=True)
class Listed:
    """A suite the change reaches, with `hits`, the reached files it covers.

    `direct` when one of the hits is a changed file; otherwise the suite is reached only
    through a file that loads a changed skill, agent or command.
    """

    suite: Suite
    hits: list[str]
    direct: bool


@dataclass(frozen=True)
class Plan:
    """The suites a change reaches, the changed plugin files none covers, and suites that fail to load."""

    suites: list[Listed]
    uncovered: list[str]
    broken: list[str]


def _references(root: pathlib.Path) -> dict[pathlib.Path, set[tuple[str, str]]]:
    path = root / "scripts" / "check-wiring.py"
    spec = importlib.util.spec_from_file_location("check_wiring", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    vars(module)["ROOT"] = root
    references: Callable[[], dict[pathlib.Path, set[tuple[str, str]]]] = module.references
    return references()


def changed_files(root: pathlib.Path, base: str) -> list[str]:
    """Files that differ from the merge base with `base`: committed, uncommitted and untracked."""

    def git(*args: str) -> str:
        return run([GIT, *args], cwd=root, capture_output=True, text=True, check=True).stdout

    merge_base = git("merge-base", base, "HEAD").strip()
    names = git("diff", "--name-only", merge_base).split()
    names += git("ls-files", "-o", "--exclude-standard").split()
    return sorted(set(names))


def target(path: str) -> tuple[str, str] | None:
    """The (plugin, name) a plugin file belongs to: its skill, agent or command."""
    parts = path.split("/")
    if len(parts) >= SKILL_DEPTH and parts[0] == "plugins" and parts[2] == "skills":
        return parts[1], parts[3]
    if len(parts) == FILE_DEPTH and parts[0] == "plugins" and parts[2] in ("agents", "commands"):
        return parts[1], parts[3].removesuffix(".md")
    return None


def expand(files: list[str], references: dict[str, set[tuple[str, str]]]) -> list[str]:
    """`files` plus every file that points, directly or through others, at a changed target."""
    reached = set(files)
    while True:
        targets = {t for f in reached if (t := target(f)) is not None}
        more = {f for f, pointed in references.items() if pointed & targets} - reached
        if not more:
            return sorted(reached)
        reached |= more


def covered_by(suite: Suite, files: list[str]) -> list[str]:
    """The files one of the suite's `covers:` globs matches."""
    return [f for f in files if any(fnmatch.fnmatch(f, glob) for glob in suite.covers)]


def listed(
    suites: list[Suite], changed: list[str], references: dict[str, set[tuple[str, str]]]
) -> list[Listed]:
    """The suites covering a changed file or a file that loads a changed target, each marked direct or not."""
    reached = expand(changed, references)
    return [
        Listed(suite, hits, direct=bool(covered_by(suite, changed)))
        for suite in suites
        if (hits := covered_by(suite, reached))
    ]


def first_gate(suite: Suite) -> str:
    """The suite's first gate model, or its first model when every one is a watch model."""
    return next((m for m in suite.models if m not in suite.watch), suite.models[0])


def make_plan(root: pathlib.Path, base: str) -> Plan:
    """The plan for the working tree against `base`."""
    plugin_files = [
        f for f in changed_files(root, base)
        if f.startswith("plugins/") and not f.endswith(UNTESTED) and GENERATED not in f
    ]  # fmt: skip
    references = {str(p.relative_to(root)): t for p, t in _references(root).items()}
    suites: list[Suite] = []
    broken: list[str] = []
    for config in sorted((root / "tests" / "evals").glob("**/suite.toml")):
        try:
            suites.append(load_suite(config.parent))
        except SuiteError as error:
            broken.append(str(error))
    needed = listed(suites, plugin_files, references)
    covered = {f for entry in needed for f in entry.hits}
    return Plan(needed, [f for f in plugin_files if f not in covered], broken)
