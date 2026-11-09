"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/readme"
COMMITS = json.loads(
    '[{"subject": "fix(tls): find the CA file on Alpine", "body": "musl images keep it at /etc/ssl/cert.pem.", "files": {"pkgsync/ca.py": "\\"\\"\\"On Alpine (musl), the CA file is /etc/ssl/cert.pem.\\"\\"\\"\\n"}}]'
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
