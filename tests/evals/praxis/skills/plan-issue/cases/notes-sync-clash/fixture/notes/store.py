"""Notes on disk: one Markdown file per note, named by its id."""

import os
from pathlib import Path


def notes_dir() -> Path:
    """Where the notes live: $NOTES_DIR, or ~/notes."""
    return Path(os.environ.get("NOTES_DIR", Path.home() / "notes"))


def add(title: str, text: str) -> int:
    """Save a new note and return its id."""
    folder = notes_dir()
    folder.mkdir(parents=True, exist_ok=True)
    ids = [int(p.stem) for p in folder.glob("*.md")]
    new_id = max(ids, default=0) + 1
    (folder / f"{new_id}.md").write_text(f"# {title}\n\n{text}\n")
    return new_id


def all_notes() -> list[tuple[int, str]]:
    """Every note's id and title, by id."""
    found = []
    for path in sorted(notes_dir().glob("*.md"), key=lambda p: int(p.stem)):
        found.append((int(path.stem), path.read_text().splitlines()[0].removeprefix("# ")))
    return found


def read(note_id: int) -> str:
    """The text of one note."""
    return (notes_dir() / f"{note_id}.md").read_text()
