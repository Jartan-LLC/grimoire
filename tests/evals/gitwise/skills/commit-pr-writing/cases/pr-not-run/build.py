"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


def commit(subject: str, body: str = "") -> None:
    git("add", "-A")
    git("commit", "-q", "-m", subject, *(["-m", body] if body else []))


def push_to_origin(*branches: str) -> None:
    git("init", "-q", "--bare", "../origin.git")
    git("remote", "add", "origin", "../origin.git")
    git("push", "-q", "-u", "origin", *branches)


git("checkout", "-q", "-b", "feature/restock")
write(
    "inventory/restock.py",
    '"""Restocking."""\n\n\ndef restock(stock: dict[str, int], sku: str, units: int) -> None:\n    """Add `units` of `sku` to `stock`."""\n    stock[sku] = stock.get(sku, 0) + units\n',
)
write(
    "tests/test_restock.py",
    'from inventory.restock import restock\n\n\ndef test_adds() -> None:\n    stock = {}\n    restock(stock, "a", 2)\n    assert stock == {"a": 2}\n',
)
write(
    "tests/test_sync.py",
    'import pytest\n\n\n@pytest.mark.skip(reason="needs Postgres")\ndef test_sync_to_warehouse() -> None:\n    ...\n',
)
commit("feat(inventory): restock a SKU", "Deliveries are booked one SKU at a time.")
