"""Build this case's history: run by the eval runner inside the fixture repository."""

import pathlib
import subprocess


def git(*args: str) -> None:
    subprocess.run(["git", *args], check=True, capture_output=True)


git("checkout", "-q", "-b", "feature/redesign")
COMMITS = [
    ("feat(ui): new upload page layout", "fileshare/templates/upload.html", "<main>new</main>\n"),
    ("wip: move file metadata into sqlite", "fileshare/meta.py", "# half done\n"),
    ("wip: dark mode", "fileshare/static/dark.css", "body { background: #111; }\n"),
]
for subject, path, text in COMMITS:
    target = pathlib.Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
    git("add", "-A")
    git("commit", "-q", "-m", subject)
