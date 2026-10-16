#!/usr/bin/env python3
"""Name the plugin release tags a commit on main owes, in the order to create them.

A version is released once it is on main (RELEASING.md), so every version that a
commit changes gets a `{plugin}--v{version}` tag at that commit. A dependency is
tagged before the plugin that needs it, because constraints resolve against these
tags. `tag-releases.yml` runs this after CI passes on a push to main, creates the
tags that do not exist yet and releases them all.

Usage: release-tags.py <base-ref> <head-ref>
Prints one tag per line; nothing when the commit changes no version.
"""

import json
import shutil
import subprocess
import sys
from dataclasses import dataclass

GIT = shutil.which("git") or "git"


@dataclass(frozen=True)
class Manifest:
    """The fields of a plugin.json that decide its release tag."""

    version: str
    dependencies: frozenset[str]


def parse_manifest(text: str) -> Manifest:
    """Read the version and dependency names from a plugin.json's text."""
    data = json.loads(text)
    names: set[str] = set()
    for dep in data.get("dependencies", []):
        names.add(dep if isinstance(dep, str) else dep["name"])
    return Manifest(version=str(data["version"]), dependencies=frozenset(names))


def due_tags(*, base: dict[str, Manifest], head: dict[str, Manifest]) -> list[str]:
    """Tags for plugins whose version differs from base, dependencies first.

    A plugin new at head counts as changed. Plugins with no ordering constraint
    between them come out by name, so the order is the same on every run.
    """
    changed = {
        name: m for name, m in head.items() if name not in base or base[name].version != m.version
    }
    order: list[str] = []
    placed: set[str] = set()
    while len(placed) < len(changed):
        ready = sorted(
            name
            for name, m in changed.items()
            if name not in placed and not (m.dependencies & (changed.keys() - placed))
        )
        if not ready:
            raise ValueError(f"dependency cycle among {sorted(changed.keys() - placed)}")
        for name in ready:
            order.append(f"{name}--v{changed[name].version}")
            placed.add(name)
    return order


def manifests_at(ref: str) -> dict[str, Manifest]:
    """Every plugin's manifest at a git ref; empty when that commit has no plugins/.

    A ref that does not name a commit raises CalledProcessError: read as "no
    plugins", a bad base would make every plugin look new.
    """
    # Argument lists, never a shell: a ref is one argv item however it is spelt.
    subprocess.run(  # noqa: S603
        [GIT, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}"],
        capture_output=True,
        check=True,
    )
    listing = subprocess.run(  # noqa: S603
        [GIT, "ls-tree", "-d", "--name-only", f"{ref}:plugins"],
        capture_output=True,
        text=True,
        check=False,
    )
    if listing.returncode != 0:
        return {}
    found: dict[str, Manifest] = {}
    for name in listing.stdout.split():
        shown = subprocess.run(  # noqa: S603
            [GIT, "show", f"{ref}:plugins/{name}/.claude-plugin/plugin.json"],
            capture_output=True,
            text=True,
            check=False,
        )
        if shown.returncode == 0:
            found[name] = parse_manifest(shown.stdout)
    return found


def main() -> int:
    """Print the tags the head commit owes."""
    try:
        base_ref, head_ref = sys.argv[1:]
    except ValueError:
        print(__doc__, file=sys.stderr)
        return 2
    for tag in due_tags(base=manifests_at(base_ref), head=manifests_at(head_ref)):
        print(tag)
    return 0


if __name__ == "__main__":
    sys.exit(main())
