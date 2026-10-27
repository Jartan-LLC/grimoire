"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/rows-module", "subject": "refactor: rename tally.parse to tally.rows", "body": "The module holds the row type next, so `rows` names it better.", "files": {"tally/report.py": "\\"\\"\\"Turn rows into totals.\\"\\"\\"\\n\\nfrom decimal import Decimal\\n\\nfrom tally.parse import parse_rows\\n\\n\\ndef total(text: str, column: str = \\"amount\\") -> Decimal:\\n    \\"\\"\\"The sum of `column` over the export\'s rows.\\"\\"\\"\\n    return sum((Decimal(row[column]) for row in parse_rows(text)), Decimal(0))\\n"}, "rename": ["tally/parse.py", "tally/rows.py"]}'
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
