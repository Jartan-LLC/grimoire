"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "docs/releasing"
COMMITS = json.loads(
    '[{"subject": "feat(release): add scripts/release.sh", "body": "", "files": {"scripts/release.sh": "#!/bin/sh\\n# release.sh VERSION: tag VERSION and push it. On HTTP 403 after a workflow change: gh auth refresh -s workflow.\\nset -eu\\n"}}, {"subject": "docs: add the release procedure", "body": "", "files": {"docs/releasing.md": "# Releasing\\n\\nRun `scripts/release.sh <version>` from `main`. It tags the version and pushes the tag.\\n\\n## Troubleshooting\\n\\nIf the push fails with HTTP 403 after a workflow file changed, run `gh auth refresh -s workflow`\\nand run the script again.\\n"}}]'
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
