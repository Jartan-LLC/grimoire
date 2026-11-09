"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/logrot"
COMMITS = json.loads(
    '[{"subject": "fix(logrot): leave an empty log unrotated", "body": "", "files": {"logrot/cli.py": "\\"\\"\\"logrot FILE [--max-size SIZE] [--keep N]: rotate FILE once it passes SIZE (default 10M), keeping N old files (default 7).\\"\\"\\"\\n# An empty log is not rotated.\\n"}}, {"subject": "fix(logrot): stop assuming rename is atomic on NFS", "body": "", "files": {"logrot/cli.py": "\\"\\"\\"logrot FILE [--max-size SIZE] [--keep N]: rotate FILE once it passes SIZE (default 10M), keeping N old files (default 7).\\"\\"\\"\\n# An empty log is not rotated.\\n# NFS rename is not atomic.\\n"}}, {"subject": "fix(logrot): leave a named pipe alone", "body": "", "files": {"logrot/cli.py": "\\"\\"\\"logrot FILE [--max-size SIZE] [--keep N]: rotate FILE once it passes SIZE (default 10M), keeping N old files (default 7).\\"\\"\\"\\n# An empty log is not rotated.\\n# NFS rename is not atomic.\\n# A FIFO given as FILE is not rotated.\\n"}}, {"subject": "docs: document the command", "body": "", "files": {"docs/rotate.md": "# Rotate a log\\n\\n`logrot app.log --max-size 10M` rotates `app.log` once it passes 10 MB, renaming it to `app.log.1`.\\n`--keep N` sets how many old files stay; the default is 5.\\n\\nAn empty log is left as it is, not rotated. On NFS, a rename is not atomic. A named pipe given\\nas FILE is left alone.\\n"}}]'
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
