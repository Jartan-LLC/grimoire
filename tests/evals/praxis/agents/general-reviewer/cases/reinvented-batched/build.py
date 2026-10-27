"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/invoice-batches", "subject": "feat(invoices): send invoices in batches of 50", "body": "The mail provider rejects requests with more than 50 recipients.", "files": {"ledger/batches.py": "\\"\\"\\"Split invoices into the batches the mail provider accepts.\\"\\"\\"\\n\\nfrom collections.abc import Iterable, Iterator\\n\\nBATCH_SIZE = 50\\n\\n\\ndef _chunks(items: Iterable[str], size: int) -> Iterator[tuple[str, ...]]:\\n    \\"\\"\\"`items` in tuples of `size`, the last one shorter when they do not divide evenly.\\"\\"\\"\\n    batch: list[str] = []\\n    for item in items:\\n        batch.append(item)\\n        if len(batch) == size:\\n            yield tuple(batch)\\n            batch = []\\n    if batch:\\n        yield tuple(batch)\\n\\n\\ndef batches(invoice_ids: Iterable[str]) -> list[tuple[str, ...]]:\\n    \\"\\"\\"The invoice ids in batches of BATCH_SIZE.\\"\\"\\"\\n    return list(_chunks(invoice_ids, BATCH_SIZE))\\n"}, "rename": null}'
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
