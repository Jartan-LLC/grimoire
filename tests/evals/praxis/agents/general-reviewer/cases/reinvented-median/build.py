"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/median-order", "subject": "feat(report): report the median order value", "body": "Finance compares the median order with the mean to spot a few large orders skewing it.", "files": {"tally/stats.py": "\\"\\"\\"Summary figures for an export.\\"\\"\\"\\n\\nfrom decimal import Decimal\\n\\nfrom tally.parse import parse_rows\\n\\n\\ndef _median(values: list[Decimal]) -> Decimal:\\n    \\"\\"\\"The middle value of `values`; the mean of the two middle ones for an even count.\\"\\"\\"\\n    ordered = sorted(values)\\n    middle = len(ordered) // 2\\n    if len(ordered) % 2:\\n        return ordered[middle]\\n    return (ordered[middle - 1] + ordered[middle]) / 2\\n\\n\\ndef median_order(text: str, column: str = \\"amount\\") -> Decimal:\\n    \\"\\"\\"The median of `column` over the export\'s rows.\\"\\"\\"\\n    return _median([Decimal(row[column]) for row in parse_rows(text)])\\n"}, "rename": null}'
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
