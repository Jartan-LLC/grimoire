"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


def write(path: str, text: str) -> None:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)


write(
    ".claude/workspace/issue-44/plan.md",
    '# Plan for #44\n\n1. In README.md, after the first paragraph, add: "Between attempts it waits 100 ms."\n2. Run the tests.\n',
)
