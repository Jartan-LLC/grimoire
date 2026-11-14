"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "docs/preview"
COMMITS = json.loads(
    '[{"subject": "feat(docs): add scripts/docs-dev.sh", "body": "", "files": {"scripts/docs-dev.sh": "#!/bin/sh\\n# docs-dev.sh: serve the site at http://localhost:5173 and rebuild each page on save.\\n# On Linux, \\"ENOSPC: System limit for number of file watchers reached\\": run\\n# sudo sysctl fs.inotify.max_user_watches=524288, then run the script again.\\nset -eu\\n[ -d node_modules ] || npm install\\nexec npx vitepress dev site --port 5173\\n"}}, {"subject": "docs: add how to preview the site", "body": "", "files": {"docs/preview.md": "# Previewing the site\\n\\nRun `scripts/docs-dev.sh` and open http://localhost:5173. Each page rebuilds when you save it.\\n\\n## Troubleshooting\\n\\nIf the script stops with \\"ENOSPC: System limit for number of file watchers reached\\" (Linux), run\\n`sudo sysctl fs.inotify.max_user_watches=524288` and run the script again.\\n"}}]'
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
