"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/refunds", "subject": "feat(refunds): compute what a refund costs the shop", "body": "Support needs the net cost of a refund before approving it.", "files": {"ledger/refunds.py": "\\"\\"\\"What refunding a charge costs the shop.\\"\\"\\"\\n\\nfrom decimal import Decimal\\n\\nfrom ledger.fees import CARD_FIXED\\n\\n\\ndef refund_cost(amount: Decimal) -> Decimal:\\n    \\"\\"\\"The fee the shop does not get back when it refunds a charge of `amount`.\\"\\"\\"\\n    # The processor keeps the fixed part of its fee when a charge is refunded.\\n    return CARD_FIXED\\n"}, "rename": null}'
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
