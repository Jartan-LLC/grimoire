"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/check-docs"
COMMITS = json.loads(
    '[{"subject": "fix(check): skip links inside fenced code blocks", "body": "", "files": {"mdcheck/cli.py": "\\"\\"\\"mdcheck [PATH...]: check every link in the Markdown files under PATH (default .); print each broken one and exit 1 if any.\\"\\"\\"\\n# Links inside fenced code blocks are skipped.\\n"}}, {"subject": "fix(check): match reference-style labels case-insensitively", "body": "", "files": {"mdcheck/cli.py": "\\"\\"\\"mdcheck [PATH...]: check every link in the Markdown files under PATH (default .); print each broken one and exit 1 if any.\\"\\"\\"\\n# Links inside fenced code blocks are skipped.\\n# Reference-style labels match case-insensitively.\\n"}}, {"subject": "fix(check): retry a 429 after its Retry-After", "body": "", "files": {"mdcheck/cli.py": "\\"\\"\\"mdcheck [PATH...]: check every link in the Markdown files under PATH (default .); print each broken one and exit 1 if any.\\"\\"\\"\\n# Links inside fenced code blocks are skipped.\\n# Reference-style labels match case-insensitively.\\n# A 429 is retried after its Retry-After.\\n"}}, {"subject": "docs: document the command", "body": "", "files": {"docs/check.md": "# Check your links\\n\\nRun `mdcheck docs/` before you push. It checks every link in the Markdown files under `docs/`,\\nprints each broken one and exits 2 if it found any, so CI can stop on it.\\n"}}]'
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
