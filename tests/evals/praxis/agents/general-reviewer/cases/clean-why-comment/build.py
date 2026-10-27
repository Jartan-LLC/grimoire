"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

CHANGE = json.loads(
    '{"branch": "fix/spaced-exports", "subject": "fix(parse): read exports that put a space after each comma", "body": "The shop\'s new export writes \\", \\" between fields, so every column after the first was keyed with a leading space and total() could not find \\"amount\\".", "files": {"tally/parse.py": "\\"\\"\\"Read the shop\'s CSV export into rows.\\"\\"\\"\\n\\nimport csv\\nimport io\\n\\n\\ndef parse_rows(text: str) -> list[dict[str, str]]:\\n    \\"\\"\\"The export\'s data rows, keyed by header, with blank lines skipped.\\"\\"\\"\\n    text = text.removeprefix(\\"\\\\ufeff\\")\\n    # The shop\'s newer exports write \\", \\" between fields; without this, every header\\n    # after the first would start with a space.\\n    rows = csv.DictReader(io.StringIO(text), skipinitialspace=True)\\n    return [row for row in rows if any(row.values())]\\n", "tests/test_parse.py": "from tally.parse import parse_rows\\n\\n\\ndef test_a_space_after_each_comma_is_dropped() -> None:\\n    assert parse_rows(\\"sku, amount\\\\na, 1.50\\\\n\\") == [{\\"sku\\": \\"a\\", \\"amount\\": \\"1.50\\"}]\\n\\n\\ndef test_blank_lines_are_skipped() -> None:\\n    assert parse_rows(\\"sku,amount\\\\n\\\\na,1.50\\\\n\\") == [{\\"sku\\": \\"a\\", \\"amount\\": \\"1.50\\"}]\\n"}, "rename": null}'
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
