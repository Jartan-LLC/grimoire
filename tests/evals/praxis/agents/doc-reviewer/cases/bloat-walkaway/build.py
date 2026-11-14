"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/walkaway"
COMMITS = json.loads(
    '[{"subject": "feat: add /autopilot:walkaway", "body": "", "files": {"commands/walkaway.md": "---\\ndescription: Run review rounds on the current PR while you are away\\n---\\n\\nRun review rounds on the current branch\'s PR until two come back clean, then stop.\\n\\nLimits:\\n\\n- Never pushes to `main`, never merges and never force-pushes.\\n- Stops after 8 rounds.\\n- Does not run on a PR from a fork.\\n- Skips the run when `gh` is logged out.\\n- Ignores draft PRs older than 30 days.\\n"}}, {"subject": "docs: add walkaway to the README", "body": "", "files": {"README.md": "# autopilot\\n\\nA Claude Code plugin that keeps work moving while you are away.\\n\\n## Install\\n\\n```text\\n/plugin install autopilot@acme\\n```\\n\\n## Commands\\n\\n- `/autopilot:walkaway` -- runs review rounds on the current PR until two come back clean. It\\n  never merges, never pushes to `main` and stops after 5 rounds.\\n  It does not run on a PR from a fork, skips the run when `gh` is logged out, and ignores draft PRs\\n  older than 30 days.\\n"}}]'
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
