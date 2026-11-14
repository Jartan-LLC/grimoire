"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/at"
COMMITS = json.loads(
    '[{"subject": "fix(at): fire a reminder set inside a DST gap at the first valid minute", "body": "A reminder set at 02:30 on the night clocks skip from 02:00 to 03:00 never fired. It now fires at 03:00.", "files": {"remind/at.py": "\\"\\"\\"remind at HH:MM NOTE. A time inside a DST gap fires at the first valid minute after it.\\"\\"\\"\\n"}}]'
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
