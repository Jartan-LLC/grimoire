"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/readme"
COMMITS = json.loads(
    '[{"subject": "fix(scan): detect and turn rotated pages", "body": "", "files": {"scan2txt/cli.py": "\\"\\"\\"scan2txt FILE.pdf [--lang CODE]: write the text of every page to FILE.txt. --lang defaults to eng.\\"\\"\\"\\n# Rotated pages are detected and turned.\\n"}}, {"subject": "fix(scan): downsample pages scanned above 600 dpi", "body": "", "files": {"scan2txt/cli.py": "\\"\\"\\"scan2txt FILE.pdf [--lang CODE]: write the text of every page to FILE.txt. --lang defaults to eng.\\"\\"\\"\\n# Rotated pages are detected and turned.\\n# Pages above 600 dpi are downsampled first.\\n"}}, {"subject": "fix(scan): skip a password-protected PDF with a message", "body": "", "files": {"scan2txt/cli.py": "\\"\\"\\"scan2txt FILE.pdf [--lang CODE]: write the text of every page to FILE.txt. --lang defaults to eng.\\"\\"\\"\\n# Rotated pages are detected and turned.\\n# Pages above 600 dpi are downsampled first.\\n# A password-protected PDF is skipped with a message.\\n"}}, {"subject": "docs: describe the change", "body": "", "files": {"README.md": "# scan2txt\\n\\nTurn scanned PDFs into text.\\n\\n## Usage\\n\\n`scan2txt letter.pdf` writes the text of every page to `letter.txt`. `--lang CODE` sets the\\nlanguage; it defaults to `deu`.\\n\\nRotated pages are detected and turned. Pages scanned above 600 dpi are downsampled first. A\\npassword-protected PDF is skipped with a message.\\n"}}]'
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
