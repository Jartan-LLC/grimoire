"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/cache"
COMMITS = json.loads(
    '[{"subject": "feat(cache): add --cache-dir", "body": "", "files": {"fetchy/cache.py": "\\"\\"\\"The download cache.\\"\\"\\"\\n"}}, {"subject": "fix(cache): lock with a lock file on NFS, where flock does nothing", "body": "", "files": {"fetchy/cache.py": "\\"\\"\\"The download cache. On NFS, flock is a no-op, so a lock file is used.\\"\\"\\"\\n"}}, {"subject": "fix(cache): shorten cache paths past Windows\' 260-character MAX_PATH", "body": "", "files": {"fetchy/cache.py": "\\"\\"\\"The download cache. On NFS, flock is a no-op, so a lock file is used.\\n\\nPaths past MAX_PATH (260) are hashed.\\n\\"\\"\\"\\n"}}, {"subject": "fix(cache): ignore entries stamped by a clock running ahead", "body": "", "files": {"fetchy/cache.py": "\\"\\"\\"The download cache. On NFS, flock is a no-op, so a lock file is used.\\n\\nPaths past MAX_PATH (260) are hashed. An entry stamped in the future is refetched.\\n\\"\\"\\"\\n"}}]'
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
