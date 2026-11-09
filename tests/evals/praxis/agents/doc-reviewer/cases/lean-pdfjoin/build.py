"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/pdfjoin"
COMMITS = json.loads(
    '[{"subject": "fix(pdfjoin): open encrypted PDFs that have an empty owner password", "body": "", "files": {"pdfjoin/cli.py": "\\"\\"\\"pdfjoin OUT IN...: join the IN files, in the order given, into OUT.\\"\\"\\"\\n# Empty owner password: opened.\\n"}}, {"subject": "fix(pdfjoin): flatten bookmarks nested deeper than 10 levels", "body": "", "files": {"pdfjoin/cli.py": "\\"\\"\\"pdfjoin OUT IN...: join the IN files, in the order given, into OUT.\\"\\"\\"\\n# Empty owner password: opened.\\n# Bookmarks deeper than 10 levels are flattened.\\n"}}, {"subject": "fix(pdfjoin): rebuild a broken xref table before joining", "body": "", "files": {"pdfjoin/cli.py": "\\"\\"\\"pdfjoin OUT IN...: join the IN files, in the order given, into OUT.\\"\\"\\"\\n# Empty owner password: opened.\\n# Bookmarks deeper than 10 levels are flattened.\\n# A broken xref table is rebuilt.\\n"}}, {"subject": "docs: document the command", "body": "", "files": {"README.md": "# pdfjoin\\n\\nJoin PDF files into one.\\n\\n## Usage\\n\\n`pdfjoin out.pdf a.pdf b.pdf` joins `a.pdf` and `b.pdf`, in alphabetical order, into `out.pdf`.\\n"}}]'
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
