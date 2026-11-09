"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/cronlite"
COMMITS = json.loads(
    '[{"subject": "fix(cronlite): skip a run while the previous one is still going", "body": "", "files": {"cronlite/cli.py": "\\"\\"\\"cronlite add SCHEDULE COMMAND | cronlite list | cronlite remove ID. SCHEDULE is a five-field cron expression in local time.\\"\\"\\"\\n# A job still running at its next start is skipped.\\n"}}, {"subject": "fix(cronlite): fall back to UTC without /etc/localtime", "body": "", "files": {"cronlite/cli.py": "\\"\\"\\"cronlite add SCHEDULE COMMAND | cronlite list | cronlite remove ID. SCHEDULE is a five-field cron expression in local time.\\"\\"\\"\\n# A job still running at its next start is skipped.\\n# No /etc/localtime (slim containers): UTC.\\n"}}, {"subject": "fix(cronlite): run a February 29 schedule only in leap years", "body": "", "files": {"cronlite/cli.py": "\\"\\"\\"cronlite add SCHEDULE COMMAND | cronlite list | cronlite remove ID. SCHEDULE is a five-field cron expression in local time.\\"\\"\\"\\n# A job still running at its next start is skipped.\\n# No /etc/localtime (slim containers): UTC.\\n# Feb 29 schedules run in leap years only.\\n"}}, {"subject": "docs: document the command", "body": "", "files": {"docs/schedule.md": "# Schedule jobs\\n\\nAdd a job with `cronlite add \\"0 9 * * 1\\" ./report.sh`; the schedule is a five-field cron\\nexpression in local time. `cronlite list` shows each job with its ID, and `cronlite rm ID`\\nremoves one.\\n"}}]'
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
