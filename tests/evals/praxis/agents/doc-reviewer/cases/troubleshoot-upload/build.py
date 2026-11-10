"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "docs/publishing"
COMMITS = json.loads(
    '[{"subject": "feat(publish): add scripts/publish.sh", "body": "", "files": {"scripts/publish.sh": "#!/bin/sh\\n# publish.sh [--chunk SIZE]: build the site and upload it. On HTTP 413 from the CDN: rerun with --chunk 50M.\\nset -eu\\n"}}, {"subject": "docs: add the publishing procedure", "body": "", "files": {"docs/publishing.md": "# Publishing the site\\n\\nRun `scripts/publish.sh` from `main`. It builds the site and uploads it to the CDN.\\n\\n## Troubleshooting\\n\\nIf the upload stops with HTTP 413, run `scripts/publish.sh --chunk 50M` to send it in parts.\\n"}}]'
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
