"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/updated-at", "subject": "feat(api): return when an item was last updated", "body": "The warehouse dashboard shows how fresh each stock level is.", "files": {"stockroom/api.py": "\\"\\"\\"The handlers the warehouse API calls.\\"\\"\\"\\n\\nfrom datetime import datetime\\n\\nfrom stockroom.store import Store\\n\\n\\ndef stock_level(store: Store, sku: str) -> int:\\n    \\"\\"\\"How many of `sku` are in stock; 0 for an unknown SKU.\\"\\"\\"\\n    item = store.get(sku)\\n    return item.quantity if item is not None else 0\\n\\n\\ndef last_updated(store: Store, sku: str) -> datetime | None:\\n    \\"\\"\\"When `sku`\'s stock level last changed, or None for an unknown SKU.\\"\\"\\"\\n    item = store.get(sku)\\n    # Timestamps are stored in UTC; convert to local time only when displaying them.\\n    return item.updated if item is not None else None\\n"}, "rename": null}'
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
