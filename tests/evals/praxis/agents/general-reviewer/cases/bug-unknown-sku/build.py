"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/reserve", "subject": "feat(api): reserve stock for an order", "body": "Checkout reserves stock before it takes payment.", "files": {"stockroom/api.py": "\\"\\"\\"The handlers the warehouse API calls.\\"\\"\\"\\n\\nfrom stockroom.store import Store\\n\\n\\ndef stock_level(store: Store, sku: str) -> int:\\n    \\"\\"\\"How many of `sku` are in stock; 0 for an unknown SKU.\\"\\"\\"\\n    item = store.get(sku)\\n    return item.quantity if item is not None else 0\\n\\n\\ndef reserve(store: Store, sku: str, wanted: int) -> bool:\\n    \\"\\"\\"Take `wanted` of `sku` out of stock; False, changing nothing, when there are not enough.\\"\\"\\"\\n    available = store.get(sku).quantity\\n    if available < wanted:\\n        return False\\n    store.put(sku, available - wanted)\\n    return True\\n"}, "rename": null}'
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
