"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "feature/verify-docs"
COMMITS = json.loads(
    '[{"subject": "fix(check): accept CRLF line endings in a checksum file", "body": "", "files": {"hashsum/cli.py": "\\"\\"\\"hashsum check FILE: check each file FILE lists against its SHA-256; print FAILED for a mismatch and exit 1 if any fail.\\"\\"\\"\\n# CRLF line endings are accepted.\\n"}}, {"subject": "fix(check): read BSD-style tag lines", "body": "", "files": {"hashsum/cli.py": "\\"\\"\\"hashsum check FILE: check each file FILE lists against its SHA-256; print FAILED for a mismatch and exit 1 if any fail.\\"\\"\\"\\n# CRLF line endings are accepted.\\n# BSD-style lines, SHA256 (file) = ..., are read.\\n"}}, {"subject": "fix(check): report a listed file that is missing as MISSING", "body": "", "files": {"hashsum/cli.py": "\\"\\"\\"hashsum check FILE: check each file FILE lists against its SHA-256; print FAILED for a mismatch and exit 1 if any fail.\\"\\"\\"\\n# CRLF line endings are accepted.\\n# BSD-style lines, SHA256 (file) = ..., are read.\\n# A listed file that is missing is reported as MISSING.\\n"}}, {"subject": "docs: describe the change", "body": "", "files": {"docs/verify.md": "# Check downloads\\n\\nRun `hashsum check SHA256SUMS` in the download directory. It prints `FAILED` for each file whose\\nchecksum does not match and exits 2 if any fail.\\n\\nA checksum file with CRLF line endings is accepted. BSD-style lines, `SHA256 (file) = ...`, are\\nread too. A listed file that is missing is reported as `MISSING`.\\n"}}]'
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
