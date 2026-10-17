#!/usr/bin/env python3
"""Which plugin versions a push to main changed, and which current versions have no tag.

`due BASE HEAD` prints the tag each version the push changed should get, one per
line, a dependency before the plugin that needs it (constraints resolve against
these tags). `untagged REF KNOWN` prints the tag of each plugin version at REF
that KNOWN, a file of tag names, does not list. release-tags.yml uses both and
decides where and when tags are created.
"""

import argparse
import json
import pathlib
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


def tag_name(manifest: Manifest) -> str:
    """The release tag for a plugin's version: `{plugin}--v{version}`."""
    return f"{manifest.name}--v{manifest.version}"


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
            order.append(tag_name(changed[name]))
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
            # due_tags matches dependency names, which are manifest names, against these
            # directory keys, and release.yml reads plugins/<tag's plugin>/ for the notes,
            # so a directory and its manifest name must agree.
            if manifest.name != name:
                raise ValueError(f"plugins/{name}/ declares name {manifest.name!r}")
            found[name] = manifest
    return found


def untagged(manifests: dict[str, Manifest], known: set[str]) -> list[str]:
    """The tag of each plugin's current version that `known` lacks, by plugin name."""
    return [tag_name(m) for _, m in sorted(manifests.items()) if tag_name(m) not in known]


def main() -> int:
    """Print the tags `due` or `untagged` names."""
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_subparsers(dest="mode", required=True)
    due = modes.add_parser("due", help="tags the push from BASE to HEAD owes")
    due.add_argument("base")
    due.add_argument("head")
    missing = modes.add_parser("untagged", help="current versions at REF with no tag")
    missing.add_argument("ref")
    missing.add_argument("known", type=pathlib.Path, help="file of tag names, one per line")
    args = parser.parse_args()
    if args.mode == "due":
        tags = due_tags(base=manifests_at(args.base), head=manifests_at(args.head))
    else:
        known = {line.strip() for line in args.known.read_text().splitlines()}
        tags = untagged(manifests_at(args.ref), known)
    for tag in tags:
        print(tag)
    return 0


if __name__ == "__main__":
    sys.exit(main())
