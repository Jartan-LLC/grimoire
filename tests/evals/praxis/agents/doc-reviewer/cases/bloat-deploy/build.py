"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/deploy"
COMMITS = json.loads(
    '[{"subject": "feat(deploy): add scripts/deploy.sh", "body": "", "files": {"scripts/deploy.sh": "#!/bin/sh\\n# Deploy the current release candidate: push the image, run migrations, switch traffic.\\nset -eu\\n"}}, {"subject": "fix(deploy): retry a 502 from the registry three times", "body": "", "files": {"scripts/deploy.sh": "#!/bin/sh\\n# Deploy the current release candidate: push the image, run migrations, switch traffic.\\nset -eu\\n# A 502 from the registry is retried three times.\\n"}}, {"subject": "fix(deploy): skip the migration step when no migration changed", "body": "", "files": {"scripts/deploy.sh": "#!/bin/sh\\n# Deploy the current release candidate: push the image, run migrations, switch traffic.\\nset -eu\\n# A 502 from the registry is retried three times.\\n# No migration changed: the migration step is skipped.\\n"}}, {"subject": "fix(deploy): fetch the tags first on a shallow clone", "body": "", "files": {"scripts/deploy.sh": "#!/bin/sh\\n# Deploy the current release candidate: push the image, run migrations, switch traffic.\\nset -eu\\n# A 502 from the registry is retried three times.\\n# No migration changed: the migration step is skipped.\\n# On a shallow clone the tags are fetched first.\\n"}}, {"subject": "docs: describe the change", "body": "", "files": {"DEPLOYING.md": "# Deploying\\n\\nEvery merge to `main` builds a release candidate.\\n\\n## Deploy a release\\n\\nRun `make deploy` from `main`. It pushes the image, runs the migrations and switches traffic to the\\nnew version. A 502 from the registry is retried three times. When no migration changed, the migration\\nstep is skipped. On a shallow clone the script fetches the tags first.\\n"}}]'
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
