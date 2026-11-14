"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/settings"
COMMITS = json.loads(
    '[{"subject": "feat(settings): add lock_timeout and fsync_every", "body": "Both are read from queue.toml.", "files": {"queue/settings.py": "\\"\\"\\"Settings, read from queue.toml.\\"\\"\\"\\n\\nDEFAULTS = {\\n    \\"workers\\": 4,  # worker processes\\n    \\"retry_limit\\": 5,  # attempts before a job fails\\n    \\"lock_timeout\\": 30,  # seconds to wait for the queue lock; raise it on slow network disks\\n    \\"fsync_every\\": 0,  # fsync the journal every N jobs; 0 leaves it to the OS\\n}\\n"}}, {"subject": "fix(settings): read a queue.toml saved with a byte order mark", "body": "Notepad writes one, and tomllib rejected the whole file.", "files": {"queue/load.py": "\\"\\"\\"Read queue.toml over the defaults.\\"\\"\\"\\n\\nimport tomllib\\nfrom pathlib import Path\\n\\nfrom .settings import DEFAULTS\\n\\n\\ndef load(path: str = \\"queue.toml\\") -> dict:\\n    # utf-8-sig drops the byte order mark Notepad writes, which tomllib rejects.\\n    return {**DEFAULTS, **tomllib.loads(Path(path).read_text(encoding=\\"utf-8-sig\\"))}\\n"}}]'
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
