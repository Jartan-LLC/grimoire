"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/bulk-put", "subject": "feat(store): set many stock levels at once", "body": "The nightly import sets every SKU in one call.", "files": {"stockroom/store.py": "# mypy: ignore-errors\\n\\"\\"\\"An in-memory store of items, keyed by SKU.\\"\\"\\"\\n\\nfrom datetime import UTC, datetime\\n\\nfrom stockroom.models import Item\\n\\n\\nclass Store:\\n    \\"\\"\\"Items by SKU.\\"\\"\\"\\n\\n    def __init__(self) -> None:\\n        \\"\\"\\"An empty store.\\"\\"\\"\\n        self._items: dict[str, Item] = {}\\n\\n    def put(self, sku: str, quantity: int) -> Item:\\n        \\"\\"\\"Set the quantity of `sku`.\\"\\"\\"\\n        item = Item(sku, quantity, datetime.now(UTC))\\n        self._items[sku] = item\\n        return item\\n\\n    def put_many(self, levels):\\n        \\"\\"\\"Set the quantity of every SKU in `levels`.\\"\\"\\"\\n        return [self.put(sku, quantity) for sku, quantity in levels.items()]\\n\\n    def get(self, sku: str) -> Item | None:\\n        \\"\\"\\"The item for `sku`, or None when it is not stocked.\\"\\"\\"\\n        return self._items.get(sku)\\n"}, "rename": null}'
)


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


git("init", "-q", "--bare", "../origin.git")
git("remote", "add", "origin", "../origin.git")
git("push", "-q", "-u", "origin", "main")
git("checkout", "-q", "-b", CHANGE["branch"])
if CHANGE["rename"]:
    git("mv", *CHANGE["rename"])
for path, text in CHANGE["files"].items():
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
git("add", "-A")
git("commit", "-q", "-m", CHANGE["subject"], "-m", CHANGE["body"])
