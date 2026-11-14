"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/deploy-key"
COMMITS = json.loads(
    '[{"subject": "feat(deploy): add a script that makes the CI deploy key", "body": "", "files": {"scripts/new-deploy-key.sh": "#!/bin/sh\\n# new-deploy-key.sh: make the SSH key pair CI deploys with, in the current directory.\\n# deploy_key is the private key: it goes only into the CI secret DEPLOY_KEY, never into git.\\nset -eu\\nssh-keygen -q -t ed25519 -N \'\' -f deploy_key\\necho \\"Add deploy_key.pub to /home/deploy/.ssh/authorized_keys on shop.acme.dev.\\"\\necho \\"Paste deploy_key into the CI secret DEPLOY_KEY.\\"\\n"}}, {"subject": "fix(deploy): stop instead of overwriting an existing deploy_key", "body": "", "files": {"scripts/new-deploy-key.sh": "#!/bin/sh\\n# new-deploy-key.sh: make the SSH key pair CI deploys with, in the current directory.\\n# deploy_key is the private key: it goes only into the CI secret DEPLOY_KEY, never into git.\\nset -eu\\nif [ -e deploy_key ]; then\\n  echo \\"deploy_key already exists here; move it away and run the script again.\\" >&2\\n  exit 1\\nfi\\nssh-keygen -q -t ed25519 -N \'\' -f deploy_key\\necho \\"Add deploy_key.pub to /home/deploy/.ssh/authorized_keys on shop.acme.dev.\\"\\necho \\"Paste deploy_key into the CI secret DEPLOY_KEY.\\"\\n"}}, {"subject": "fix(deploy): name the key deploy@acme-shop, not its maker\'s user@host", "body": "ssh-keygen\'s default comment names the machine the key was made on, and it ends up in\\nthe server\'s authorized_keys.", "files": {"scripts/new-deploy-key.sh": "#!/bin/sh\\n# new-deploy-key.sh: make the SSH key pair CI deploys with, in the current directory.\\n# deploy_key is the private key: it goes only into the CI secret DEPLOY_KEY, never into git.\\nset -eu\\nif [ -e deploy_key ]; then\\n  echo \\"deploy_key already exists here; move it away and run the script again.\\" >&2\\n  exit 1\\nfi\\nssh-keygen -q -t ed25519 -N \'\' -C deploy@acme-shop -f deploy_key\\necho \\"Add deploy_key.pub to /home/deploy/.ssh/authorized_keys on shop.acme.dev.\\"\\necho \\"Paste deploy_key into the CI secret DEPLOY_KEY.\\"\\n"}}, {"subject": "fix(deploy): find ssh-keygen in Git Bash on Windows", "body": "", "files": {"scripts/new-deploy-key.sh": "#!/bin/sh\\n# new-deploy-key.sh: make the SSH key pair CI deploys with, in the current directory.\\n# deploy_key is the private key: it goes only into the CI secret DEPLOY_KEY, never into git.\\nset -eu\\nif [ -e deploy_key ]; then\\n  echo \\"deploy_key already exists here; move it away and run the script again.\\" >&2\\n  exit 1\\nfi\\ncommand -v ssh-keygen >/dev/null 2>&1 || PATH=\\"$PATH:/c/Windows/System32/OpenSSH\\"\\nssh-keygen -q -t ed25519 -N \'\' -C deploy@acme-shop -f deploy_key\\necho \\"Add deploy_key.pub to /home/deploy/.ssh/authorized_keys on shop.acme.dev.\\"\\necho \\"Paste deploy_key into the CI secret DEPLOY_KEY.\\"\\n"}}]'
)


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


git("checkout", "-q", "-b", BRANCH)
for commit in COMMITS:
    for path, text in commit["files"].items():
        target = pathlib.Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        if target.suffix == ".sh":
            target.chmod(0o755)
    git("add", "-A")
    git("commit", "-q", "-m", commit["subject"], "-m", commit["body"])
