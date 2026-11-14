"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/sync-run"
COMMITS = json.loads(
    '[{"subject": "fix(sync): remove a lock file a killed run left behind", "body": "A run killed mid-copy left .sync.lock, and every later run refused to start. A lock older than an hour is now removed.", "files": {"sync/run.py": "\\"\\"\\"Copy new and changed files from SOURCE to TARGET.\\"\\"\\"\\n\\nimport time\\nfrom pathlib import Path\\n\\nLOCK = Path(\\".sync.lock\\")\\n\\n\\ndef run(source: str, target: str) -> int:\\n    return 0\\n\\n\\ndef clear_stale_lock() -> None:\\n    \\"\\"\\"Remove a lock a killed run left more than an hour ago.\\"\\"\\"\\n    if LOCK.exists() and time.time() - LOCK.stat().st_mtime > 3600:\\n        LOCK.unlink()\\n"}}]'
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
