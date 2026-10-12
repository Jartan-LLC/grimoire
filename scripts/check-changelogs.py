#!/usr/bin/env python3
"""Check that every plugin's CHANGELOG.md has an entry for its current version.

A version bump without an entry fails here, so the entry lands with the bump.
`--notes <plugin> <version>` prints that version's entry instead, for the
GitHub Release body.
"""

import argparse
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def section(changelog: str, version: str) -> str:
    """The text under `## <version>`, up to the next `## ` heading; empty if none."""
    lines = changelog.split("\n")
    try:
        start = lines.index(f"## {version}") + 1
    except ValueError:
        return ""
    end = next((i for i in range(start, len(lines)) if lines[i].startswith("## ")), len(lines))
    return "\n".join(lines[start:end]).strip()


def problems() -> list[str]:
    """One message per plugin whose changelog lacks a current-version entry."""
    found: list[str] = []
    for manifest in sorted(ROOT.glob("plugins/*/.claude-plugin/plugin.json")):
        plugin = manifest.parent.parent
        version = json.loads(manifest.read_text())["version"]
        changelog = plugin / "CHANGELOG.md"
        name = plugin.relative_to(ROOT)
        if not changelog.is_file():
            found.append(f"{name}: no CHANGELOG.md")
        elif not section(changelog.read_text(), version):
            found.append(f"{name}/CHANGELOG.md: no entry under '## {version}'")
    return found


def main() -> int:
    """Check every plugin, or with `--notes` print one version's entry."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--notes", nargs=2, metavar=("PLUGIN", "VERSION"))
    args = parser.parse_args()

    if args.notes:
        plugin, version = args.notes
        changelog = ROOT / "plugins" / plugin / "CHANGELOG.md"
        entry = section(changelog.read_text(), version) if changelog.is_file() else ""
        if not entry:
            print(f"plugins/{plugin}/CHANGELOG.md has no entry for {version}", file=sys.stderr)
            return 1
        print(entry)
        return 0

    found = problems()
    for message in found:
        print(message)
    if found:
        return 1
    print("every plugin changelog has its current version")
    return 0


if __name__ == "__main__":
    sys.exit(main())
