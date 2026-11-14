"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/worker-docs"
COMMITS = json.loads(
    '[{"subject": "fix(worker): drop a job with no payload, with a log line", "body": "", "files": {"jobq/worker.py": "\\"\\"\\"jobq work [--concurrency N]: run jobs from the queue, N at a time. --concurrency defaults to 8.\\"\\"\\"\\n# A job with no payload is dropped, with a log line.\\n"}}, {"subject": "fix(worker): finish the current job on SIGTERM", "body": "", "files": {"jobq/worker.py": "\\"\\"\\"jobq work [--concurrency N]: run jobs from the queue, N at a time. --concurrency defaults to 8.\\"\\"\\"\\n# A job with no payload is dropped, with a log line.\\n# On SIGTERM the current job is finished first.\\n"}}, {"subject": "fix(worker): follow MOVED replies from a Redis cluster", "body": "", "files": {"jobq/worker.py": "\\"\\"\\"jobq work [--concurrency N]: run jobs from the queue, N at a time. --concurrency defaults to 8.\\"\\"\\"\\n# A job with no payload is dropped, with a log line.\\n# On SIGTERM the current job is finished first.\\n# MOVED replies from a Redis cluster are followed.\\n"}}, {"subject": "docs: describe the change", "body": "", "files": {"docs/worker.md": "# Run a worker\\n\\n`jobq work` takes jobs from the queue and runs them, 4 at a time unless you pass `--concurrency N`.\\nStop it with Ctrl-C.\\n\\nA job with no payload is dropped with a log line. On SIGTERM the worker finishes its current job\\nfirst. MOVED replies from a Redis cluster are followed.\\n"}}]'
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
