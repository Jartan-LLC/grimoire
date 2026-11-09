"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/readme"
COMMITS = json.loads(
    '[{"subject": "fix(init): say so when the home directory is read-only", "body": "", "files": {"tally/init.py": "\\"\\"\\"tally init. On a read-only home directory it exits with: error: EROFS, cannot write ~/.tally\\"\\"\\"\\n"}}]'
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
