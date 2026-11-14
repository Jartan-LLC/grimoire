"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/dry-run"
COMMITS = json.loads(
    '[{"subject": "feat(release): add --dry-run", "body": "Prints the tag it would make and stops.", "files": {"scripts/release.sh": "#!/bin/sh\\n# release.sh [--dry-run] VERSION: tag VERSION and push it; --dry-run prints the tag and stops.\\nset -eu\\n"}}, {"subject": "fix(release): exit 3 when --dry-run meets a tag that exists", "body": "It prints `already tagged` instead of a stack trace.", "files": {"scripts/exit_codes.txt": "3: already tagged (--dry-run on an existing tag)\\n"}}]'
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
