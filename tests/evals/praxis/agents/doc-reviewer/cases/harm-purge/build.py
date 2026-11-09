"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/purge"
COMMITS = json.loads(
    '[{"subject": "feat(prune): add --purge", "body": "", "files": {"snap/cli.py": "\\"\\"\\"snap prune [--keep N | --purge]: --purge deletes every snapshot and the history file; this cannot be undone.\\"\\"\\"\\n"}}, {"subject": "fix(prune): skip a snapshot whose directory vanished mid-prune", "body": "", "files": {"snap/prune.py": "\\"\\"\\"A snapshot whose directory vanished mid-prune is skipped.\\"\\"\\"\\n"}}, {"subject": "docs: document prune", "body": "", "files": {"docs/usage.md": "# Usage\\n\\n## snap prune\\n\\n`snap prune --keep N` keeps the newest `N` snapshots. `snap prune --purge` clears every snapshot and\\nthe history.\\n"}}]'
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
