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


def accepts(constraint: str, version: str) -> bool | None:
    """Whether a dependency range accepts a version; None for a range form not handled.

    Handles the forms the plugins use: `^X.Y.Z`, `~X.Y.Z` and an exact `X.Y.Z`. A
    prerelease suffix is ignored on both sides.
    """

    def triple(text: str) -> tuple[int, int, int] | None:
        parts = text.split("-", 1)[0].split(".")
        if len(parts) != 3 or not all(part.isdigit() for part in parts):  # noqa: PLR2004
            return None
        return int(parts[0]), int(parts[1]), int(parts[2])

    have = triple(version)
    kind, floor = (
        (constraint[0], triple(constraint[1:]))
        if constraint[:1] in "^~"
        else ("=", triple(constraint))
    )
    if have is None or floor is None:
        return None
    if kind == "=":
        return have == floor
    if kind == "~":
        ceiling = (floor[0], floor[1] + 1, 0)
    elif floor[0] > 0:
        ceiling = (floor[0] + 1, 0, 0)
    else:
        ceiling = (0, floor[1] + 1, 0)
    return floor <= have < ceiling


def problems() -> list[str]:
    """One message per problem found.

    The problems: no plugin manifests, a manifest without a version, a changelog
    without that version's entry, a directory named unlike its manifest, or a
    dependency range that rejects (or cannot read) the version of a plugin in
    this tree.
    """
    manifests = sorted(ROOT.glob("plugins/*/.claude-plugin/plugin.json"))
    if not manifests:
        return ["no plugins/*/.claude-plugin/plugin.json found -- nothing was checked"]
    found: list[str] = []
    data = {manifest: json.loads(manifest.read_text()) for manifest in manifests}
    versions = {m.parent.parent.name: d.get("version") for m, d in data.items()}
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
        for dep in fields.get("dependencies", []):
            if not isinstance(dep, dict):
                continue  # a bare name accepts any version
            entry = cast("dict[str, object]", dep)
            name, wanted = entry.get("name"), entry.get("version")
            have = versions.get(name) if isinstance(name, str) else None
            if not isinstance(wanted, str) or not isinstance(have, str):
                continue  # no range, or a plugin from outside this tree
            verdict = accepts(wanted, have)
            if verdict is None:
                found.append(f"{where}: cannot read the range {wanted!r} for {name}")
            elif not verdict:
                found.append(f"{where}: needs {name} {wanted}, but {name} here is {have}")
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
