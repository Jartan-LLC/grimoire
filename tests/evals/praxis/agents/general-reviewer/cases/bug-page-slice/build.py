"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/paging", "subject": "feat(report): page through rows", "body": "The web view shows an export 25 rows at a time.", "files": {"tally/pages.py": "\\"\\"\\"Show an export a page at a time.\\"\\"\\"\\n\\nfrom tally.parse import parse_rows\\n\\n\\ndef page(text: str, number: int, size: int = 25) -> list[dict[str, str]]:\\n    \\"\\"\\"The rows on page `number` (counting from 1), `size` rows to a page.\\"\\"\\"\\n    rows = parse_rows(text)\\n    start = (number - 1) * size\\n    return rows[start : start + size - 1]\\n"}, "rename": null}'
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
