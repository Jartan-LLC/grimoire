"""Project lint: every function in src/ declares its return type."""

import ast
import pathlib
import sys

bad = [
    f"{path}:{node.lineno}: {node.name} has no return annotation"
    for path in sorted(pathlib.Path("src").rglob("*.py"))
    for node in ast.walk(ast.parse(path.read_text()))
    if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef) and node.returns is None
]
for line in bad:
    print(line)
sys.exit(1 if bad else 0)
