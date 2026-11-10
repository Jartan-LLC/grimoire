"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/gc-delete"
COMMITS = json.loads(
    '[{"subject": "feat(gc): add --delete", "body": "", "files": {"attic/cli.py": "\\"\\"\\"attic gc [--delete]: list attachments no note links to. --delete removes them from disk; this cannot be undone.\\"\\"\\"\\n"}}, {"subject": "fix(gc): match an attachment name with a trailing space", "body": "", "files": {"attic/names.py": "\\"\\"\\"An attachment name with a trailing space is matched as written.\\"\\"\\"\\n"}}, {"subject": "docs: document --delete", "body": "", "files": {"docs/gc.md": "# Clean up attachments\\n\\n`attic gc` lists the attachments no note links to.\\n\\nAdd `--delete` to remove them.\\n"}}]'
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
