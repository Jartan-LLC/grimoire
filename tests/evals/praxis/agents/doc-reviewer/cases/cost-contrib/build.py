"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "docs/readme"
COMMITS = json.loads(
    '[{"subject": "fix: count words joined by a non-breaking space as two", "body": "", "files": {"tally/words.py": "\\"\\"\\"Words joined by a non-breaking space (U+00A0) count as two.\\"\\"\\"\\n"}}, {"subject": "docs: add usage to the README", "body": "", "files": {"README.md": "# tally\\n\\nCount words in Markdown files. See [Contributing](CONTRIBUTING.md) to work on it.\\n\\n## Usage\\n\\n`tally docs/` prints the word count of each Markdown file under `docs/`.\\n"}}]'
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
