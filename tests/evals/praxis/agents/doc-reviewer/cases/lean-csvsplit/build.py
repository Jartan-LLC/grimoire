"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/split-docs"
COMMITS = json.loads(
    '[{"subject": "fix(split): keep a quoted field with a line break in one part", "body": "", "files": {"csvsplit/cli.py": "\\"\\"\\"csvsplit FILE [--rows N]: split FILE into FILE.1.csv, FILE.2.csv, ... of N rows each, each with the header. --rows defaults to 1000.\\"\\"\\"\\n# A quoted field holding a line break stays whole.\\n"}}, {"subject": "fix(split): write a byte order mark into the first part only", "body": "", "files": {"csvsplit/cli.py": "\\"\\"\\"csvsplit FILE [--rows N]: split FILE into FILE.1.csv, FILE.2.csv, ... of N rows each, each with the header. --rows defaults to 1000.\\"\\"\\"\\n# A quoted field holding a line break stays whole.\\n# A BOM goes into the first part only.\\n"}}, {"subject": "fix(split): ignore an empty last line", "body": "", "files": {"csvsplit/cli.py": "\\"\\"\\"csvsplit FILE [--rows N]: split FILE into FILE.1.csv, FILE.2.csv, ... of N rows each, each with the header. --rows defaults to 1000.\\"\\"\\"\\n# A quoted field holding a line break stays whole.\\n# A BOM goes into the first part only.\\n# An empty last line is ignored.\\n"}}, {"subject": "docs: document the command", "body": "", "files": {"docs/split.md": "# Split a CSV file\\n\\n`csvsplit orders.csv` writes `orders.1.csv`, `orders.2.csv` and so on, each with the header row.\\nEach part holds 10000 rows unless you pass `--rows N`.\\n"}}]'
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
