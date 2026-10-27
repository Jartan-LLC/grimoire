"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/stale-items", "subject": "feat(api): list items not updated for a day", "body": "The warehouse team recounts any SKU whose stock level has not changed in 24 hours.", "files": {"stockroom/api.py": "\\"\\"\\"The handlers the warehouse API calls.\\"\\"\\"\\n\\nfrom datetime import UTC, datetime, timedelta\\n\\nfrom stockroom.store import Store\\n\\nSTALE_AFTER = timedelta(hours=24)\\n\\n\\ndef stock_level(store: Store, sku: str) -> int:\\n    \\"\\"\\"How many of `sku` are in stock; 0 for an unknown SKU.\\"\\"\\"\\n    item = store.get(sku)\\n    return item.quantity if item is not None else 0\\n\\n\\ndef stale_skus(store: Store, sku_list: list[str]) -> list[str]:\\n    \\"\\"\\"The SKUs in `sku_list` whose stock level has not changed for STALE_AFTER.\\"\\"\\"\\n    now = datetime.now(UTC)\\n    # Store.put stamps every item with datetime.now(UTC), so `updated` is always timezone-aware.\\n    return [\\n        sku for sku in sku_list\\n        if (item := store.get(sku)) is not None and now - item.updated > STALE_AFTER\\n    ]\\n"}, "rename": null}'
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
