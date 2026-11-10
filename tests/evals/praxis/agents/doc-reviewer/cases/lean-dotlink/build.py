"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/dotlink"
COMMITS = json.loads(
    '[{"subject": "feat(dotlink): link the dotfiles at container start", "body": "", "files": {"src/dotlink/install.sh": "#!/bin/sh\\n# Link each file in /opt/dotfiles into $HOME; keep a file it replaces as <file>.orig.\\nset -eu\\nfor f in /opt/dotfiles/.[!.]*; do\\n  t=\\"$HOME/$(basename \\"$f\\")\\"\\n  [ -e \\"$t\\" ] && mv \\"$t\\" \\"$t.orig\\"\\n  ln -s \\"$f\\" \\"$t\\"\\ndone\\n"}}, {"subject": "fix(dotlink): leave a target that already links to its dotfile", "body": "", "files": {"src/dotlink/install.sh": "#!/bin/sh\\n# Link each file in /opt/dotfiles into $HOME; keep a file it replaces as <file>.orig.\\nset -eu\\nfor f in /opt/dotfiles/.[!.]*; do\\n  t=\\"$HOME/$(basename \\"$f\\")\\"\\n  [ -e \\"$t\\" ] && mv \\"$t\\" \\"$t.orig\\"\\n  ln -s \\"$f\\" \\"$t\\"\\ndone\\n# A target that already links to its dotfile is left as is.\\n"}}, {"subject": "fix(dotlink): never overwrite an existing .orig", "body": "", "files": {"src/dotlink/install.sh": "#!/bin/sh\\n# Link each file in /opt/dotfiles into $HOME; keep a file it replaces as <file>.orig.\\nset -eu\\nfor f in /opt/dotfiles/.[!.]*; do\\n  t=\\"$HOME/$(basename \\"$f\\")\\"\\n  [ -e \\"$t\\" ] && mv \\"$t\\" \\"$t.orig\\"\\n  ln -s \\"$f\\" \\"$t\\"\\ndone\\n# A target that already links to its dotfile is left as is.\\n# An existing <file>.orig is never overwritten.\\n"}}, {"subject": "fix(dotlink): skip a dotfile whose target is a directory", "body": "", "files": {"src/dotlink/install.sh": "#!/bin/sh\\n# Link each file in /opt/dotfiles into $HOME; keep a file it replaces as <file>.orig.\\nset -eu\\nfor f in /opt/dotfiles/.[!.]*; do\\n  t=\\"$HOME/$(basename \\"$f\\")\\"\\n  [ -e \\"$t\\" ] && mv \\"$t\\" \\"$t.orig\\"\\n  ln -s \\"$f\\" \\"$t\\"\\ndone\\n# A target that already links to its dotfile is left as is.\\n# An existing <file>.orig is never overwritten.\\n# A target that is a directory is skipped, with a message.\\n"}}, {"subject": "docs: document the command", "body": "", "files": {"src/dotlink/README.md": "# dotlink\\n\\nA Dev Container Feature that links your dotfiles into every container.\\n\\n## Install\\n\\n```json\\n\\"features\\": {\\n  \\"ghcr.io/acme/features/dotlink:1\\": {}\\n}\\n```\\n\\n## What it changes\\n\\nMount your dotfiles repository at `/opt/dotfiles` first. When the container starts, dotlink links each\\nfile in it into your home directory. A file it replaces is kept as `<file>.bak`; move it back to undo\\nthe link.\\n"}}]'
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
