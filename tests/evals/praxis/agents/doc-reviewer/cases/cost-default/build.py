"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/timeout"
COMMITS = json.loads(
    '[{"subject": "feat(cli): add --timeout", "body": "", "files": {"fetchy/cli.py": "\\"\\"\\"fetchy URL [--timeout SECONDS]: download URL. --timeout defaults to 60 seconds.\\"\\"\\"\\n"}}, {"subject": "fix(cli): retry once when an old proxy rejects a TLS session ticket", "body": "", "files": {"fetchy/tls.py": "\\"\\"\\"Retry once when an old proxy rejects a TLS session ticket.\\"\\"\\"\\n"}}, {"subject": "docs: document --timeout", "body": "", "files": {"docs/usage.md": "# Usage\\n\\n`fetchy URL` downloads `URL` into the current directory.\\n\\n`--timeout SECONDS` sets how long to wait for the server. It defaults to 30 seconds.\\n"}}]'
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
