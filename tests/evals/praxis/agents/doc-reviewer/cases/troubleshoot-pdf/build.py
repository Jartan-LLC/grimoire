"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib
import subprocess

BRANCH = "docs/pdf"
COMMITS = json.loads(
    '[{"subject": "feat(pdf): add scripts/build-pdf.sh", "body": "pandoc hands each page\'s images to XeLaTeX, which cannot read WebP: a page that links a\\n.webp image stops the build with \\"Unknown graphics extension: .webp\\". Converting the image\\nto PNG (`magick <image>.webp <image>.png`) and linking the PNG fixes it.", "files": {"scripts/build-pdf.sh": "#!/bin/sh\\n# build-pdf.sh: build handbook.pdf from the pages in site/.\\nset -eu\\npandoc site/*.md --pdf-engine=xelatex -o handbook.pdf\\n", ".gitignore": "handbook.pdf\\n"}}, {"subject": "docs: add how to build the PDF", "body": "", "files": {"docs/pdf.md": "# Building the PDF\\n\\nYou need pandoc and a TeX distribution with XeLaTeX. From the repository root, run\\n`scripts/build-pdf.sh`. It writes `handbook.pdf` there.\\n\\n## Troubleshooting\\n\\nIf the build stops with \\"Unknown graphics extension: .webp\\", a page links a WebP image, which\\nXeLaTeX cannot read. Convert it with `magick <image>.webp <image>.png`, link the PNG instead, and\\nrun the script again.\\n"}}]'
)


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


git("checkout", "-q", "-b", BRANCH)
for commit in COMMITS:
    for path, text in commit["files"].items():
        target = pathlib.Path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(text)
        if target.suffix == ".sh":
            target.chmod(0o755)
    git("add", "-A")
    git("commit", "-q", "-m", commit["subject"], "-m", commit["body"])
