"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/export"
COMMITS = json.loads(
    '[{"subject": "fix(export): keep the dotless i in a Turkish locale", "body": "str.upper() in tr_TR changed i.", "files": {"ledger/export.py": "\\"\\"\\"ledger export --format csv|json [--out FILE]: write every entry to FILE (default stdout).\\"\\"\\"\\n# tr_TR: the dotless i is kept as is.\\n"}}, {"subject": "fix(export): write the repeated hour twice when daylight saving time ends", "body": "", "files": {"ledger/export.py": "\\"\\"\\"ledger export --format csv|json [--out FILE]: write every entry to FILE (default stdout).\\"\\"\\"\\n# tr_TR: the dotless i is kept as is.\\n# DST end: the repeated hour is written twice.\\n"}}, {"subject": "fix(export): write amounts above 2^53 as strings in JSON", "body": "", "files": {"ledger/export.py": "\\"\\"\\"ledger export --format csv|json [--out FILE]: write every entry to FILE (default stdout).\\"\\"\\"\\n# tr_TR: the dotless i is kept as is.\\n# DST end: the repeated hour is written twice.\\n# JSON: amounts above 2^53 are strings.\\n"}}]'
)


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


git("checkout", "-q", "-b", BRANCH)
for commit in COMMITS:
    for path, text in commit["files"].items():
        target = pathlib.Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
    git("add", "-A")
    git("commit", "-q", "-m", commit["subject"], "-m", commit["body"])
