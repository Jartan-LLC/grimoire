"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "feature/semicolon-exports", "subject": "feat(parse): read semicolon-separated exports", "body": "The EU shop exports with semicolons.", "files": {"tally/parse.py": "\\"\\"\\"Read the shop\'s CSV export into rows.\\"\\"\\"\\n\\nimport csv\\nimport io\\n\\n\\ndef parse_rows(text: str) -> list[dict[str, str]]:\\n    \\"\\"\\"The export\'s data rows, keyed by header, with blank lines skipped.\\"\\"\\"\\n    text = text.removeprefix(\\"\\\\ufeff\\")\\n    delimiter = \\";\\" if text.split(\\"\\\\n\\", 1)[0].count(\\";\\") > text.split(\\"\\\\n\\", 1)[0].count(\\",\\") else \\",\\"\\n    # TODO: handle exports that mix delimiters\\n    rows = csv.DictReader(io.StringIO(text), delimiter=delimiter)\\n    return [row for row in rows if any(row.values())]\\n"}, "rename": null}'
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
