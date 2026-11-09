"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/settings"
COMMITS = json.loads(
    '[{"subject": "feat(settings): add lock_timeout and fsync_every", "body": "Both are read from queue.toml.", "files": {"queue/settings.py": "\\"\\"\\"Settings, read from queue.toml.\\"\\"\\"\\n\\nDEFAULTS = {\\n    \\"workers\\": 4,  # worker processes\\n    \\"retry_limit\\": 5,  # attempts before a job fails\\n    \\"lock_timeout\\": 30,  # seconds to wait for the queue lock; raise it on slow network disks\\n    \\"fsync_every\\": 0,  # fsync the journal every N jobs; 0 leaves it to the OS\\n}\\n"}}, {"subject": "fix(settings): round a lock_timeout below 1 up to 1", "body": "0 made every lock attempt fail at once.", "files": {"queue/clamp.py": "\\"\\"\\"A lock_timeout below 1 is rounded up to 1.\\"\\"\\"\\n"}}]'
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
