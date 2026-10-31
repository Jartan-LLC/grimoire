"""Project lint: every test says what it checks, in a docstring."""

import ast
import pathlib
import sys

bad = [
    f"{path}:{node.lineno}: {node.name} has no docstring"
    for path in sorted(pathlib.Path("tests").rglob("test_*.py"))
    for node in ast.walk(ast.parse(path.read_text()))
    if isinstance(node, ast.FunctionDef) and node.name.startswith("test_") and ast.get_docstring(node) is None
]
for line in bad:
    print(line)
sys.exit(1 if bad else 0)
