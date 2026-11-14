"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/envcheck"
COMMITS = json.loads(
    '[{"subject": "fix(envcheck): ignore a byte order mark", "body": "", "files": {"envcheck/cli.py": "\\"\\"\\"envcheck [EXAMPLE]: list the variables EXAMPLE (default .env.example) names that .env lacks. Exits 1 when any are missing.\\"\\"\\"\\n# A BOM at the start of a file is ignored.\\n"}}, {"subject": "fix(envcheck): accept CRLF line endings", "body": "", "files": {"envcheck/cli.py": "\\"\\"\\"envcheck [EXAMPLE]: list the variables EXAMPLE (default .env.example) names that .env lacks. Exits 1 when any are missing.\\"\\"\\"\\n# A BOM at the start of a file is ignored.\\n# CRLF line endings are accepted.\\n"}}, {"subject": "fix(envcheck): keep the last value of a variable defined twice", "body": "", "files": {"envcheck/cli.py": "\\"\\"\\"envcheck [EXAMPLE]: list the variables EXAMPLE (default .env.example) names that .env lacks. Exits 1 when any are missing.\\"\\"\\"\\n# A BOM at the start of a file is ignored.\\n# CRLF line endings are accepted.\\n# Defined twice: the last value wins.\\n"}}]'
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
