#!/usr/bin/env python3
"""Fail a plugin changed since the branch left `--base REF` whose version did not change.

Installs that have that version would never get the change. A plugin changed when
any tracked file under plugins/<name>/ but its CHANGELOG.md differs from the merge
base of REF and HEAD, the working tree included.
"""

import argparse
import json
import pathlib
import shutil
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent
GIT = shutil.which("git") or "git"


def git(*args: str) -> subprocess.CompletedProcess[str]:
    """Run git in ROOT with these arguments, capturing its output as text."""
    # Argument lists, never a shell: a ref is one argv item however it is spelt.
    return subprocess.run(  # noqa: S603
        [GIT, "-C", str(ROOT), *args], capture_output=True, text=True, check=False
    )


def unbumped(base: str) -> list[str]:
    """One message per plugin changed since the branch left `base` but not bumped.

    Compares the working tree with the merge base of `base` and HEAD, so changes
    `base` gained after the branch left it stay out. A plugin changed when any
    tracked file under plugins/<name>/ but its CHANGELOG.md differs, generated Codex
    files included: RELEASING.md's bump rule covers them. A plugin new since the merge
    base, or removed, has no version to keep and is skipped.

    Raises:
        ValueError: `base` has no merge base with HEAD, or git cannot diff against it,
            so nothing could be compared.
    """
    fork = git("merge-base", base, "HEAD")
    if fork.returncode != 0:
        detail = fork.stderr.strip() or "no common commit"
        raise ValueError(
            f"--base {base}: no merge base with HEAD ({detail});"
            " pass a ref this checkout has, such as origin/main (make: BASE=<ref>)"
        )
    commit = fork.stdout.strip()
    diff = git(
        "diff",
        "--name-only",
        "--no-renames",
        "-z",
        commit,
        "--",
        "plugins/",
        ":(glob,exclude)plugins/*/CHANGELOG.md",
    )
    if diff.returncode != 0:
        raise ValueError(f"--base {base}: git diff failed ({diff.stderr.strip()})")
    changed = sorted(
        {path.split("/")[1] for path in diff.stdout.split("\0") if path.count("/") > 1}
    )
    found: list[str] = []
    for name in changed:
        manifest = ROOT / "plugins" / name / ".claude-plugin" / "plugin.json"
        before = git("show", f"{commit}:plugins/{name}/.claude-plugin/plugin.json")
        if not manifest.is_file() or before.returncode != 0:
            continue
        version = json.loads(manifest.read_text()).get("version")
        if version == json.loads(before.stdout).get("version"):
            found.append(
                f"plugins/{name}: changed since {base}, but its version is still {version}:"
                " bump it in .claude-plugin/plugin.json"
            )
    return found


def main() -> int:
    """Check every plugin changed since `--base` for a new version."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", metavar="REF", required=True)
    args = parser.parse_args()

    try:
        found = unbumped(args.base)
    except ValueError as error:
        found = [str(error)]
    for message in found:
        print(message)
    if found:
        return 1
    print(f"every plugin changed since {args.base} has a new version")
    return 0


if __name__ == "__main__":
    sys.exit(main())
