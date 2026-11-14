"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "docs/publishing"
COMMITS = json.loads(
    '[{"subject": "feat(publish): add scripts/publish.sh", "body": "", "files": {"scripts/publish.sh": "#!/bin/sh\\n# publish.sh [--chunk SIZE]: build the site and upload it. On HTTP 413 from the CDN: rerun with --chunk 50M.\\nset -eu\\nurl=https://upload.cdn.example.com/acme-site\\ntrap \'rm -f site.tar.gz site.tar.gz.part-*\' EXIT\\nnpx @11ty/eleventy --input=site --output=dist\\ntar -czf site.tar.gz -C dist .\\nif [ \\"${1:-}\\" = \\"--chunk\\" ]; then\\n  split -b \\"${2:?--chunk needs a size, such as 50M}\\" site.tar.gz site.tar.gz.part-\\n  for part in site.tar.gz.part-*; do\\n    curl --fail --silent --show-error -T \\"$part\\" \\"$url/$part\\"\\n  done\\nelse\\n  curl --fail --silent --show-error -T site.tar.gz \\"$url/site.tar.gz\\"\\nfi\\n"}}, {"subject": "docs: add the publishing procedure", "body": "", "files": {"docs/publishing.md": "# Publishing the site\\n\\nRun `scripts/publish.sh` from `main`. It builds the site and uploads it to the CDN.\\n\\n## Troubleshooting\\n\\nIf the upload stops with HTTP 413, run `scripts/publish.sh --chunk 50M` to send it in parts.\\n"}}]'
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
