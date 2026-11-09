"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/at"
COMMITS = json.loads(
    '[{"subject": "fix(at): fire a reminder set inside a DST gap at the first valid minute", "body": "", "files": {"remind/at.py": "\\"\\"\\"remind at HH:MM NOTE: a time already past today is set for tomorrow.\\"\\"\\"\\n"}}, {"subject": "docs: say what a reminder in a DST gap does", "body": "", "files": {"README.md": "# remind\\n\\nSchedule desktop reminders.\\n\\n## Usage\\n\\n`remind at 14:30 \\"stand-up\\"` shows a reminder at 14:30 today, or never if 14:30 has passed.\\n\\nA reminder set inside the hour skipped when daylight saving time starts fires at the first valid\\nminute after it.\\n"}}]'
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
