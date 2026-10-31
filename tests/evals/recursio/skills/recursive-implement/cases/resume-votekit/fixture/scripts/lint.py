# SPDX-License-Identifier: MIT
"""Project lint: every Python file starts with the SPDX line."""

import pathlib
import sys

LINE = "# SPDX-License-Identifier: MIT"

bad = [
    path
    for root in ("src", "tests", "scripts")
    for path in sorted(pathlib.Path(root).rglob("*.py"))
    if not path.read_text().startswith(LINE + "\n")
]
for path in bad:
    print(f"{path}: the first line must be {LINE!r}")
sys.exit(1 if bad else 0)
