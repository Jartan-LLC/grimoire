"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/pack-docs"
COMMITS = json.loads(
    '[{"subject": "docs: document the command", "body": "", "files": {"docs/usage.md": "# Usage\\n\\n`pack photos` writes `photos.tar` holding every file under `photos/`.\\n"}}, {"subject": "fix(pack): write zip64 records for a file over 4 GiB", "body": "Plain zip records stop at 4 GiB.", "files": {"pack/cli.py": "\\"\\"\\"pack DIR: write DIR.zip holding every file under DIR.\\"\\"\\"\\n\\n# A file over 4 GiB is written with zip64 records.\\n"}}]'
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
