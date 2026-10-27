"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/line-discounts", "subject": "feat(invoices): discount each unit on an invoice line", "body": "Promotions take a fixed amount off every unit.", "files": {"ledger/lines.py": "\\"\\"\\"Invoice lines.\\"\\"\\"\\n\\nfrom decimal import Decimal\\n\\nfrom ledger.money import to_cents\\n\\n\\ndef line_total(unit_price: Decimal, quantity: int, unit_discount: Decimal) -> Decimal:\\n    \\"\\"\\"What a line costs: `quantity` units, each `unit_discount` off `unit_price`.\\"\\"\\"\\n    return to_cents(unit_price - unit_discount * quantity)\\n"}, "rename": null}'
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
