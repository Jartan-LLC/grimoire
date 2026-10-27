"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/wire-fee", "subject": "feat(fees): add the flat wire transfer fee", "body": "Wire payments carry a flat bank fee, passed on at cost.", "files": {"ledger/fees.py": "\\"\\"\\"Fees charged on an invoice.\\"\\"\\"\\n\\nfrom decimal import Decimal\\n\\nfrom ledger.money import to_cents\\n\\nCARD_RATE = Decimal(\\"0.029\\")\\nCARD_FIXED = Decimal(\\"0.30\\")\\nWIRE_FIXED = Decimal(\\"15.00\\")\\n\\n\\ndef card_fee(amount: Decimal) -> Decimal:\\n    \\"\\"\\"The card processor\'s fee on a charge of `amount`.\\"\\"\\"\\n    return to_cents(amount * CARD_RATE + CARD_FIXED)\\n\\n\\ndef wire_fee() -> Decimal:\\n    \\"\\"\\"The bank\'s flat fee on a wire transfer, whatever its amount.\\"\\"\\"\\n    return WIRE_FIXED\\n", "tests/test_fees.py": "from decimal import Decimal\\n\\nfrom ledger.fees import card_fee, wire_fee\\n\\n\\ndef test_card_fee_rounds_to_cents() -> None:\\n    assert card_fee(Decimal(\\"10.00\\")) == Decimal(\\"0.59\\")\\n\\n\\ndef test_wire_fee_is_flat() -> None:\\n    assert wire_fee() == Decimal(\\"15.00\\")\\n"}, "rename": null}'
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
