# Copyright (c) 2026 The brewkit authors.
"""Project lint: every Python file starts with the copyright line."""

import pathlib
import sys

LINE = "# Copyright (c) 2026 The brewkit authors."

bad = [
    path
    for root in ("src", "tests", "scripts")
    for path in sorted(pathlib.Path(root).rglob("*.py"))
    if not path.read_text().startswith(LINE + "\n")
]
for path in bad:
    print(f"{path}: the first line must be {LINE!r}")
sys.exit(1 if bad else 0)
