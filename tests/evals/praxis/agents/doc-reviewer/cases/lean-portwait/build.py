"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/wait-howto"
COMMITS = json.loads(
    '[{"subject": "fix(wait): keep waiting while the host has no route yet", "body": "", "files": {"portwait/cli.py": "\\"\\"\\"portwait HOST:PORT [--timeout SECONDS]: wait until HOST:PORT accepts a TCP connection; exit 1 on timeout. --timeout defaults to 60.\\"\\"\\"\\n# No route to the host yet (EHOSTUNREACH) counts as not ready.\\n"}}, {"subject": "fix(wait): retry a failed DNS lookup until the timeout", "body": "", "files": {"portwait/cli.py": "\\"\\"\\"portwait HOST:PORT [--timeout SECONDS]: wait until HOST:PORT accepts a TCP connection; exit 1 on timeout. --timeout defaults to 60.\\"\\"\\"\\n# No route to the host yet (EHOSTUNREACH) counts as not ready.\\n# A failed DNS lookup is retried until the timeout.\\n"}}, {"subject": "fix(wait): count a connection reset right after accept as not ready", "body": "", "files": {"portwait/cli.py": "\\"\\"\\"portwait HOST:PORT [--timeout SECONDS]: wait until HOST:PORT accepts a TCP connection; exit 1 on timeout. --timeout defaults to 60.\\"\\"\\"\\n# No route to the host yet (EHOSTUNREACH) counts as not ready.\\n# A failed DNS lookup is retried until the timeout.\\n# A reset right after accept counts as not ready.\\n"}}, {"subject": "docs: document the command", "body": "", "files": {"docs/wait.md": "# Wait for a service to start\\n\\nIn a start script, run `portwait db:5432` before the step that needs the database. It returns\\nonce `db:5432` accepts a connection, or exits 1 after 30 seconds. Pass `--timeout SECONDS` to wait\\nlonger.\\n"}}]'
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
