"""Find local changes."""

import pathlib


def changed(root: pathlib.Path, since: float) -> list[pathlib.Path]:
    """Files under `root` modified after `since`."""
    return [p for p in root.rglob("*") if p.is_file() and p.stat().st_mtime > since]
