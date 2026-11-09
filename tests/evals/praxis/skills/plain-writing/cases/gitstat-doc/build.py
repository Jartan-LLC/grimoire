"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/gitstat"
COMMITS = json.loads(
    '[{"subject": "fix(gitstat): merge mailmap entries whose emails differ only in case", "body": "", "files": {"gitstat/cli.py": "\\"\\"\\"gitstat authors [--after DATE]: commits per author, most first; --after counts only commits after DATE.\\"\\"\\"\\n# Emails are compared case-insensitively.\\n"}}, {"subject": "fix(gitstat): warn on a shallow clone", "body": "", "files": {"gitstat/cli.py": "\\"\\"\\"gitstat authors [--after DATE]: commits per author, most first; --after counts only commits after DATE.\\"\\"\\"\\n# Emails are compared case-insensitively.\\n# A shallow clone counts only the commits it has, with a warning.\\n"}}, {"subject": "fix(gitstat): count commits with no author email as unknown", "body": "", "files": {"gitstat/cli.py": "\\"\\"\\"gitstat authors [--after DATE]: commits per author, most first; --after counts only commits after DATE.\\"\\"\\"\\n# Emails are compared case-insensitively.\\n# A shallow clone counts only the commits it has, with a warning.\\n# No author email: counted as unknown.\\n"}}]'
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
