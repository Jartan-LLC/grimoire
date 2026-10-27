"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/refund-fee", "subject": "feat(fees): refund the percentage part of a card fee", "body": "The processor returns its percentage on a refund but keeps the fixed part.", "files": {"ledger/fees.py": "\\"\\"\\"Fees charged on an invoice.\\"\\"\\"\\n\\nfrom decimal import Decimal\\n\\nfrom ledger.money import to_cents\\n\\nCARD_RATE = Decimal(\\"0.029\\")\\nCARD_FIXED = Decimal(\\"0.30\\")\\n\\n\\ndef card_fee(amount: Decimal) -> Decimal:\\n    \\"\\"\\"The card processor\'s fee on a charge of `amount`.\\"\\"\\"\\n    return to_cents(amount * CARD_RATE + CARD_FIXED)\\n\\n\\ndef refunded_fee(amount: Decimal) -> Decimal:\\n    \\"\\"\\"The part of the card fee the processor returns when `amount` is refunded.\\"\\"\\"\\n    # Replaced the old float maths with Decimal here, as in card_fee.\\n    return to_cents(amount * CARD_RATE)\\n"}, "rename": null}'
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
