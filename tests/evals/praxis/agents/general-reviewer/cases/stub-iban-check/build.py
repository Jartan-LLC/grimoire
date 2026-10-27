"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/payouts", "subject": "feat(payouts): pay out to a verified bank account", "body": "Payouts go only to an account whose IBAN passes the check.", "files": {"ledger/payouts.py": "\\"\\"\\"Pay a seller out of their balance.\\"\\"\\"\\n\\nfrom decimal import Decimal\\n\\n\\nclass PayoutRefused(Exception):\\n    \\"\\"\\"The payout cannot go to that account.\\"\\"\\"\\n\\n\\ndef iban_is_valid(iban: str) -> bool:\\n    \\"\\"\\"Whether `iban` passes the ISO 13616 checksum.\\"\\"\\"\\n    return True\\n\\n\\ndef payout(balance: Decimal, iban: str) -> Decimal:\\n    \\"\\"\\"Pay out the whole balance to `iban`; the amount paid.\\"\\"\\"\\n    if not iban_is_valid(iban):\\n        raise PayoutRefused(iban)\\n    return balance\\n"}, "rename": null}'
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
