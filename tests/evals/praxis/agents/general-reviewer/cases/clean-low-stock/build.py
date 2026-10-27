"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/low-stock", "subject": "feat(api): list the SKUs running low", "body": "The buyers\' morning report lists every SKU at or below its reorder point.", "files": {"stockroom/store.py": "\\"\\"\\"An in-memory store of items, keyed by SKU.\\"\\"\\"\\n\\nfrom datetime import UTC, datetime\\n\\nfrom stockroom.models import Item\\n\\n\\nclass Store:\\n    \\"\\"\\"Items by SKU.\\"\\"\\"\\n\\n    def __init__(self) -> None:\\n        \\"\\"\\"An empty store.\\"\\"\\"\\n        self._items: dict[str, Item] = {}\\n\\n    def put(self, sku: str, quantity: int) -> Item:\\n        \\"\\"\\"Set the quantity of `sku`.\\"\\"\\"\\n        item = Item(sku, quantity, datetime.now(UTC))\\n        self._items[sku] = item\\n        return item\\n\\n    def get(self, sku: str) -> Item | None:\\n        \\"\\"\\"The item for `sku`, or None when it is not stocked.\\"\\"\\"\\n        return self._items.get(sku)\\n\\n    def items(self) -> list[Item]:\\n        \\"\\"\\"Every stocked item, in SKU order.\\"\\"\\"\\n        return [self._items[sku] for sku in sorted(self._items)]\\n", "stockroom/api.py": "\\"\\"\\"The handlers the warehouse API calls.\\"\\"\\"\\n\\nfrom stockroom.store import Store\\n\\n\\ndef stock_level(store: Store, sku: str) -> int:\\n    \\"\\"\\"How many of `sku` are in stock; 0 for an unknown SKU.\\"\\"\\"\\n    item = store.get(sku)\\n    return item.quantity if item is not None else 0\\n\\n\\ndef low_stock(store: Store, reorder_point: int) -> list[str]:\\n    \\"\\"\\"The SKUs with `reorder_point` or fewer in stock, in SKU order.\\"\\"\\"\\n    return [item.sku for item in store.items() if item.quantity <= reorder_point]\\n", "tests/test_api.py": "from stockroom.api import low_stock, stock_level\\nfrom stockroom.store import Store\\n\\n\\ndef test_stock_level_of_a_stocked_sku() -> None:\\n    store = Store()\\n    store.put(\\"a\\", 4)\\n    assert stock_level(store, \\"a\\") == 4\\n\\n\\ndef test_low_stock_includes_the_reorder_point() -> None:\\n    store = Store()\\n    store.put(\\"b\\", 2)\\n    store.put(\\"a\\", 5)\\n    store.put(\\"c\\", 9)\\n    assert low_stock(store, 5) == [\\"a\\", \\"b\\"]\\n"}, "rename": null}'
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
