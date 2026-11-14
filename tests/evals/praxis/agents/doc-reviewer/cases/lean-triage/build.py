"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/triage"
COMMITS = json.loads(
    '[{"subject": "feat: add /nightly:triage", "body": "", "files": {"commands/triage.md": "---\\ndescription: Label new issues while you are away\\n---\\n\\nLabel each new issue in the current repository by its content, then stop.\\n\\nLimits:\\n\\n- Never closes, locks or comments on an issue.\\n- Labels at most 20 issues a run.\\n- Skips a locked issue.\\n- Skips issues opened by bots.\\n- Ignores issues older than 90 days.\\n"}}, {"subject": "docs: document the command", "body": "", "files": {"README.md": "# nightly\\n\\nA Claude Code plugin for unattended repository chores.\\n\\n## Install\\n\\n```text\\n/plugin install nightly@acme\\n```\\n\\n## Commands\\n\\n- `/nightly:triage` -- labels each new issue by its content. It never closes or comments on an\\n  issue and labels at most 25 issues a run.\\n  See `commands/triage.md` for all its limits.\\n"}}]'
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
