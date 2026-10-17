#!/usr/bin/env python3
"""Check each plugin's manifest: its changelog entry, its name and its dependencies.

A version bump without an entry fails here, so the entry lands with the bump. So
does a plugin directory named unlike its plugin.json, and a dependency range that
rejects the depended-on plugin's version in the same tree: release tagging relies
on both (scripts/release-tags.py), and each would only show after merge.
`--notes <plugin> <version>` prints that version's entry instead, for the
GitHub Release body.
"""

import argparse
import json
import pathlib
import sys
from typing import cast

ROOT = pathlib.Path(__file__).resolve().parent.parent


def section(changelog: str, version: str) -> str:
    """The text under `## <version>`, up to the next `## ` heading; empty if none."""
    lines = [line.rstrip() for line in changelog.split("\n")]
    try:
        start = lines.index(f"## {version}") + 1
    except ValueError:
        return ""
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[start:end]).strip()


def missing_entry(plugin: pathlib.Path, version: str) -> str:
    """Why the plugin's changelog has no entry for `version`; empty when it has one."""
    changelog = plugin / "CHANGELOG.md"
    name = plugin.relative_to(ROOT)
    if not changelog.is_file():
        return f"{name}: no CHANGELOG.md"
    if not section(changelog.read_text(), version):
        return (
            f"{name}/CHANGELOG.md: no entry under a '## {version}' heading"
            " (the version alone, matching plugin.json)"
        )
    return ""


SEMVER_CORE = 3  # MAJOR.MINOR.PATCH


def accepts(constraint: str, version: str) -> bool | None:
    """Whether a dependency range accepts a version, as node-semver decides; None if unchecked.

    Reads `^X.Y.Z`, `~X.Y.Z` and an exact `X.Y.Z` or `=X.Y.Z`, the forms make verify
    supports. As in node-semver, which Claude Code resolves ranges with, a
    prerelease version is accepted only by a range that opts into prereleases on the
    same X.Y.Z; that case is left unchecked (None) rather than ordered here, as is a
    version with build metadata.
    """

    def split(text: str) -> tuple[tuple[int, int, int] | None, str]:
        core, _, pre = text.partition("-")
        parts = core.split(".")
        # node-semver rejects a leading zero in a numeric part ("01").
        if len(parts) != SEMVER_CORE or not all(
            part.isdigit() and (part == "0" or not part.startswith("0")) for part in parts
        ):
            return None, pre
        return (int(parts[0]), int(parts[1]), int(parts[2])), pre

    if not constraint:
        return None
    kind, body = (constraint[0], constraint[1:]) if constraint[0] in "^~=" else ("=", constraint)
    floor, floor_pre = split(body)
    have, have_pre = split(version)
    if have is None or floor is None:
        return None
    if have_pre:
        return None if floor_pre and have == floor else False
    if kind == "=":
        return have == floor and not floor_pre
    if kind == "~":
        ceiling = (floor[0], floor[1] + 1, 0)
    elif floor[0] > 0:
        ceiling = (floor[0] + 1, 0, 0)
    elif floor[1] > 0:
        ceiling = (0, floor[1] + 1, 0)
    else:
        ceiling = (0, 0, floor[2] + 1)
    return floor <= have < ceiling


def dependency_problems(
    where: str, fields: dict[str, object], versions: dict[str, object], own: str = ""
) -> list[str]:
    """One message per dependency entry that is malformed, or whose range the tree fails.

    A bare name accepts any version. An entry naming another marketplace than `own`,
    this repository's, or a plugin not in this tree, is not checked: only `versions`,
    this tree's, can answer it.
    """
    found: list[str] = []
    deps = fields.get("dependencies", [])
    if not isinstance(deps, list):
        return [f"{where}: dependencies is not a list"]
    for dep in cast("list[object]", deps):
        if isinstance(dep, str):
            continue
        entry = cast("dict[str, object]", dep) if isinstance(dep, dict) else {}
        name, wanted = entry.get("name"), entry.get("version")
        if not isinstance(name, str):
            found.append(f"{where}: a dependency that is neither a name nor an object with one")
            continue
        have = versions.get(name)
        if "version" in entry and not isinstance(wanted, str):
            found.append(f"{where}: the version range for {name} is not a string")
            continue
        foreign = "marketplace" in entry and entry["marketplace"] != own
        if foreign or not isinstance(wanted, str) or not isinstance(have, str):
            continue
        verdict = accepts(wanted, have)
        if verdict is None:
            found.append(f"{where}: cannot check the range {wanted!r} for {name} {have}")
        elif not verdict:
            found.append(f"{where}: needs {name} {wanted}, but {name} here is {have}")
    return found


def problems() -> list[str]:
    """One message per problem found.

    The problems: no plugin manifests, a manifest without a version, a changelog
    without that version's entry, a directory named unlike its manifest, or a
    dependency range that rejects (or cannot be checked against) the version of a plugin in
    this tree.
    """
    manifests = sorted(ROOT.glob("plugins/*/.claude-plugin/plugin.json"))
    if not manifests:
        return ["no plugins/*/.claude-plugin/plugin.json found -- nothing was checked"]
    found: list[str] = []
    data = {manifest: json.loads(manifest.read_text()) for manifest in manifests}
    versions = {m.parent.parent.name: d.get("version") for m, d in data.items()}
    catalog = ROOT / ".claude-plugin" / "marketplace.json"
    own = json.loads(catalog.read_text()).get("name", "") if catalog.is_file() else ""
    for manifest, fields in data.items():
        plugin = manifest.parent.parent
        where = manifest.relative_to(ROOT)
        version = fields.get("version")
        if not isinstance(version, str):
            found.append(f"{where}: no version")
        elif message := missing_entry(plugin, version):
            found.append(message)
        if fields.get("name") != plugin.name:
            found.append(f"{where}: name {fields.get('name')!r} differs from its directory")
        found.extend(dependency_problems(str(where), fields, versions, own))
    return found


def main() -> int:
    """Check every plugin, or with `--notes` print one version's entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notes", nargs=2, metavar=("PLUGIN", "VERSION"))
    args = parser.parse_args()

    if args.notes:
        name, version = args.notes
        plugin = ROOT / "plugins" / name
        if message := missing_entry(plugin, version):
            print(message, file=sys.stderr)
            return 1
        print(section((plugin / "CHANGELOG.md").read_text(), version))
        return 0

    found = problems()
    for message in found:
        print(message)
    if found:
        return 1
    print("every plugin has its changelog entry, its own name and dependency ranges that hold")
    return 0


if __name__ == "__main__":
    sys.exit(main())
