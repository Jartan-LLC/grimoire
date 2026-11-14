"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/mirror"
COMMITS = json.loads(
    '[{"subject": "feat(sync): add --mirror", "body": "", "files": {"marks/cli.py": "\\"\\"\\"marks sync [--mirror]: merge local bookmarks with the server\'s. --mirror makes the local set match the server: it deletes every local bookmark the server lacks, and this cannot be undone.\\"\\"\\"\\n"}}, {"subject": "fix(sync): accept a server clock more than 5 minutes off", "body": "", "files": {"marks/clock.py": "\\"\\"\\"A server clock more than 5 minutes off no longer fails the sync.\\"\\"\\"\\n"}}, {"subject": "docs: document --mirror", "body": "", "files": {"docs/sync.md": "# Sync\\n\\n`marks sync` merges your local bookmarks with the server\'s: a bookmark added on either side ends up on both.\\n\\nAdd `--mirror` to make your local bookmarks match the server\'s exactly.\\n"}}]'
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
