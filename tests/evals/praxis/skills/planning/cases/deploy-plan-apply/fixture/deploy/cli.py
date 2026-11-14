"""Deploy the static site: `plan` shows what would change, `apply` uploads it."""

import pathlib


def changed_files(root, remote):
    return sorted(p for p in pathlib.Path(root).rglob("*") if p.is_file() and p.name not in remote)


def plan(root, remote):
    for path in changed_files(root, remote):
        print("would upload", path)


def apply(root, remote, upload):
    for path in changed_files(root, remote):
        upload(path)
