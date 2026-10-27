"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/restock", "subject": "feat(store): add stock to an item", "body": "Deliveries add to the stock level instead of replacing it.", "files": {"stockroom/store.py": "\\"\\"\\"An in-memory store of items, keyed by SKU.\\"\\"\\"\\n\\nfrom datetime import UTC, datetime\\n\\nfrom stockroom.models import Item\\n\\n\\nclass Store:\\n    \\"\\"\\"Items by SKU.\\"\\"\\"\\n\\n    def __init__(self) -> None:\\n        \\"\\"\\"An empty store.\\"\\"\\"\\n        self._items: dict[str, Item] = {}\\n\\n    def put(self, sku: str, quantity: int) -> Item:\\n        \\"\\"\\"Set the quantity of `sku`.\\"\\"\\"\\n        item = Item(sku, quantity, datetime.now(UTC))\\n        self._items[sku] = item\\n        return item\\n\\n    def restock(self, sku: str, delivered: int) -> Item:\\n        \\"\\"\\"Add `delivered` to the stock of `sku`.\\"\\"\\"\\n        current = self._items.get(sku)\\n        print(\\"DEBUG restock\\", sku, current, delivered)\\n        return self.put(sku, (current.quantity if current else 0) + delivered)\\n\\n    def get(self, sku: str) -> Item | None:\\n        \\"\\"\\"The item for `sku`, or None when it is not stocked.\\"\\"\\"\\n        return self._items.get(sku)\\n"}, "rename": null}'
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
