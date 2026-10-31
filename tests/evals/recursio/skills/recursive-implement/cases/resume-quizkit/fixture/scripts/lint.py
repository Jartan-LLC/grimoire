"""Project lint: every Python file opens with a module docstring."""

import ast
import pathlib
import sys

bad = [
    path
    for root in ("src", "tests", "scripts")
    for path in sorted(pathlib.Path(root).rglob("*.py"))
    if ast.get_docstring(ast.parse(path.read_text())) is None
]
for path in bad:
    print(f"{path}: no module docstring")
sys.exit(1 if bad else 0)
