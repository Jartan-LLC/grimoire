"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/prune"
COMMITS = json.loads(
    '[{"subject": "fix(prune): skip a snapshot whose directory vanished mid-prune", "body": "A second prune running at the same time could remove a directory first.", "files": {"snap/prune.py": "\\"\\"\\"Prune snapshots. A snapshot whose directory vanished mid-prune is skipped.\\"\\"\\"\\n"}}]'
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
