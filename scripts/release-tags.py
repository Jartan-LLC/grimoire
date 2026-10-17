#!/usr/bin/env python3
"""Name the plugin release tags a push to main owes, in the order to create them.

A version is released once it is on main (RELEASING.md), so every version that a
push changes gets a `{plugin}--v{version}` tag at the push's tip. A dependency is
tagged before the plugin that needs it, because constraints resolve against these
tags. `release-tags.yml`, which ci.yml's release-tags job calls on a push to main,
runs this, creates the tags that do not exist yet and releases them all.

Usage: release-tags.py <base-ref> <head-ref>  (the push's base and its tip)
Prints one tag per line; nothing when the push changes no version.

       release-tags.py --current <ref>
Prints the tag each plugin's version at <ref> should have, so the workflow can
warn about a version an earlier push left untagged.
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

    name: str
    version: str
    dependencies: frozenset[str]


def parse_manifest(text: str) -> Manifest:
    """Read the version and dependency names from a plugin.json's text."""
    data = json.loads(text)
    names: set[str] = set()
    for dep in data.get("dependencies", []):
        names.add(dep if isinstance(dep, str) else dep["name"])
    return Manifest(
        name=str(data["name"]), version=str(data["version"]), dependencies=frozenset(names)
    )


def tag_name(name: str, manifest: Manifest) -> str:
    """The release tag for a plugin's version: `{plugin}--v{version}`."""
    return f"{name}--v{manifest.version}"


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
            order.append(tag_name(name, changed[name]))
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
            manifest = parse_manifest(shown.stdout)
            # Dependencies and `claude plugin tag` name a plugin by its manifest name,
            # and the tag uses the directory name: they must agree.
            if manifest.name != name:
                raise ValueError(f"plugins/{name}/ declares name {manifest.name!r}")
            found[name] = manifest
    return found


def current_tags(manifests: dict[str, Manifest]) -> list[str]:
    """The tag each plugin's current version should have, by plugin name."""
    return [tag_name(name, m) for name, m in sorted(manifests.items())]


def main() -> int:
    """Print the tags the push from base to head owes, or with --current every plugin's."""
    args = sys.argv[1:]
    if len(args) == 2 and args[0] == "--current":  # noqa: PLR2004
        for tag in current_tags(manifests_at(args[1])):
            print(tag)
        return 0
    try:
        base_ref, head_ref = args
    except ValueError:
        print(__doc__, file=sys.stderr)
        return 2
    for tag in due_tags(base=manifests_at(base_ref), head=manifests_at(head_ref)):
        print(tag)
    return 0


if __name__ == "__main__":
    sys.exit(main())
