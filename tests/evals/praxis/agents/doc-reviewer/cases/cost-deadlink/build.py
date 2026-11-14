"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "docs/readme"
COMMITS = json.loads(
    '[{"subject": "fix: stop at the body\'s end when Content-Length is larger than the body", "body": "", "files": {"fetchy/body.py": "\\"\\"\\"A Content-Length larger than the body ends at the body.\\"\\"\\"\\n"}}, {"subject": "docs: add usage to the README", "body": "", "files": {"README.md": "# fetchy\\n\\nDownload files with retries. See [Setup](docs/setup.md) for proxies.\\n\\n## Usage\\n\\n`fetchy URL` downloads `URL`.\\n"}}]'
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
