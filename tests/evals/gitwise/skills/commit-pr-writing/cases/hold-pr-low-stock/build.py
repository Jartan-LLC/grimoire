"""Build this case's history: a pushed feature branch, run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


git("init", "-q", "--bare", "-b", "main", "../origin.git")
git("remote", "add", "origin", "../origin.git")
git("push", "-q", "-u", "origin", "main")
git("checkout", "-q", "-b", "feature/low-stock")
write(
    "inventory/stock.py",
    '"""Low-stock alerts."""\n\n\ndef low_stock(items: dict[str, int], threshold: int) -> list[str]:\n    """Items with fewer than `threshold` units, by name."""\n    return sorted(name for name, units in items.items() if units < threshold)\n',
)
write(
    "tests/test_stock.py",
    'from inventory.stock import low_stock\n\n\ndef test_low() -> None:\n    assert low_stock({"a": 1, "b": 9}, 5) == ["a"]\n',
)
git("add", "-A")
git(
    "commit",
    "-q",
    "-m",
    "feat(inventory): list items low on stock",
    "-m",
    "The warehouse reorders by hand from a printout; this gives it the list.",
)
git("push", "-q", "-u", "origin", "feature/low-stock")
