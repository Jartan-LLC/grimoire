"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/post"
COMMITS = json.loads(
    '[{"subject": "feat: add /standup:post", "body": "", "files": {"commands/post.md": "---\\ndescription: Post yesterday\'s work as a standup message\\n---\\n\\nSummarise the commits and merged PRs of the last working day and post them to the team channel.\\n\\nLimits:\\n\\n- Posts at most once a day.\\n- Never posts to a channel it has not been added to.\\n- Skips weekends and the holidays in the team calendar.\\n- Leaves out commits made by bots.\\n"}}, {"subject": "docs: describe the change", "body": "", "files": {"README.md": "# standup\\n\\nA Claude Code plugin that writes the daily standup.\\n\\n## Install\\n\\n```text\\n/plugin install standup@acme\\n```\\n\\n## Commands\\n\\n- `/standup:post` -- posts the commits and merged PRs of the last working day to the team channel.\\n  It posts at most twice a day and never to a channel it has not been added to. It skips weekends\\n  and the holidays in the team calendar, and leaves out commits made by bots.\\n"}}]'
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
