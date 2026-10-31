"""Project lint: every module in src/ declares its public names in __all__."""

import ast
import pathlib
import sys

__all__: list[str] = []


def declares_all(path: pathlib.Path) -> bool:
    """Whether the module assigns __all__ at its top level."""
    for node in ast.parse(path.read_text()).body:
        targets = node.targets if isinstance(node, ast.Assign) else [getattr(node, "target", None)]
        if any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets):
            return True
    return False


bad = [path for path in sorted(pathlib.Path("src").rglob("*.py")) if not declares_all(path)]
for path in bad:
    print(f"{path}: no __all__")
sys.exit(1 if bad else 0)
