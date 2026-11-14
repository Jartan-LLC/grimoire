"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/watch"
COMMITS = json.loads(
    '[{"subject": "fix(watch): poll when the tree passes fs.inotify.max_user_watches", "body": "", "files": {"notes/watch.py": "\\"\\"\\"notes watch DIR: rebuild the index whenever a note in DIR changes. Stop it with Ctrl-C.\\"\\"\\"\\n# Past fs.inotify.max_user_watches, fall back to polling.\\n"}}, {"subject": "fix(watch): see a note saved by renaming a temporary file", "body": "vim saves that way.", "files": {"notes/watch.py": "\\"\\"\\"notes watch DIR: rebuild the index whenever a note in DIR changes. Stop it with Ctrl-C.\\"\\"\\"\\n# Past fs.inotify.max_user_watches, fall back to polling.\\n# vim saves by renaming a temporary file: treated as a new file.\\n"}}, {"subject": "fix(watch): poll a network drive every 5 seconds", "body": "", "files": {"notes/watch.py": "\\"\\"\\"notes watch DIR: rebuild the index whenever a note in DIR changes. Stop it with Ctrl-C.\\"\\"\\"\\n# Past fs.inotify.max_user_watches, fall back to polling.\\n# vim saves by renaming a temporary file: treated as a new file.\\n# Network drives send no events: poll every 5 seconds.\\n"}}]'
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
