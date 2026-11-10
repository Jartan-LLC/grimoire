"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/thumbs"
COMMITS = json.loads(
    '[{"subject": "fix(thumbs): use the first frame of an animated PNG", "body": "", "files": {"thumbs/cli.py": "\\"\\"\\"thumbs DIR [--size PX]: write a thumbnail of every JPEG and PNG in DIR into DIR/.thumbs/. --size defaults to 256.\\"\\"\\"\\n# An animated PNG uses its first frame.\\n"}}, {"subject": "fix(thumbs): reduce 16-bit PNGs to 8 bits", "body": "", "files": {"thumbs/cli.py": "\\"\\"\\"thumbs DIR [--size PX]: write a thumbnail of every JPEG and PNG in DIR into DIR/.thumbs/. --size defaults to 256.\\"\\"\\"\\n# An animated PNG uses its first frame.\\n# 16-bit PNGs are reduced to 8 bits.\\n"}}, {"subject": "fix(thumbs): skip a file whose name holds a newline, with a message", "body": "", "files": {"thumbs/cli.py": "\\"\\"\\"thumbs DIR [--size PX]: write a thumbnail of every JPEG and PNG in DIR into DIR/.thumbs/. --size defaults to 256.\\"\\"\\"\\n# An animated PNG uses its first frame.\\n# 16-bit PNGs are reduced to 8 bits.\\n# A file whose name holds a newline is skipped.\\n"}}, {"subject": "docs: document the command", "body": "", "files": {"README.md": "# thumbs\\n\\nMake thumbnails for a photo folder.\\n\\n## Usage\\n\\n`thumbs photos/` writes a thumbnail of every JPEG and PNG in `photos/` into `photos/thumbs/`.\\n`--size PX` sets the longest side; it defaults to 256.\\n"}}]'
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
