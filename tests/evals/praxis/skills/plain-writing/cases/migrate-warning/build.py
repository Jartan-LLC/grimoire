"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/drop-unused"
COMMITS = json.loads(
    '[{"subject": "fix(migrate): emulate DROP COLUMN on SQLite before 3.35", "body": "", "files": {"db/sqlite_compat.py": "\\"\\"\\"SQLite before 3.35 has no DROP COLUMN; the table is rebuilt instead.\\"\\"\\"\\n"}}]'
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
