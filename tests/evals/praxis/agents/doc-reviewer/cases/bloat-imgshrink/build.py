"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/imgshrink"
COMMITS = json.loads(
    '[{"subject": "fix(imgshrink): convert CMYK JPEGs to RGB", "body": "", "files": {"imgshrink/cli.py": "\\"\\"\\"imgshrink DIR [--quality N]: re-encode every JPEG and PNG in DIR in place. --quality defaults to 80.\\"\\"\\"\\n# CMYK JPEGs are converted to RGB.\\n"}}, {"subject": "fix(imgshrink): apply the EXIF orientation before dropping EXIF", "body": "", "files": {"imgshrink/cli.py": "\\"\\"\\"imgshrink DIR [--quality N]: re-encode every JPEG and PNG in DIR in place. --quality defaults to 80.\\"\\"\\"\\n# CMYK JPEGs are converted to RGB.\\n# EXIF orientation is applied first.\\n"}}, {"subject": "fix(imgshrink): skip files over 100 MB with a message", "body": "", "files": {"imgshrink/cli.py": "\\"\\"\\"imgshrink DIR [--quality N]: re-encode every JPEG and PNG in DIR in place. --quality defaults to 80.\\"\\"\\"\\n# CMYK JPEGs are converted to RGB.\\n# EXIF orientation is applied first.\\n# Files over 100 MB are skipped.\\n"}}, {"subject": "docs: document the command", "body": "", "files": {"README.md": "# imgshrink\\n\\nShrink images for the web.\\n\\n## Usage\\n\\n`imgshrink photos/` re-encodes every JPEG and PNG in `photos/` in place. `--quality N` sets the\\nJPEG quality; it defaults to 75.\\n\\nCMYK JPEGs are converted to RGB. An EXIF orientation is applied before the EXIF data is dropped.\\nFiles over 100 MB are skipped with a message.\\n"}}]'
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
