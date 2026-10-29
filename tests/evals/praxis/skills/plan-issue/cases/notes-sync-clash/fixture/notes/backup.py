"""Copy every note to a backup folder."""

import os
import shutil
from pathlib import Path

from notes.store import notes_dir


def backup_dir() -> Path:
    """Where backups go: $NOTES_BACKUP_DIR, or ~/notes-backup."""
    return Path(os.environ.get("NOTES_BACKUP_DIR", Path.home() / "notes-backup"))


def copy_all() -> int:
    """Copy every note to the backup folder; return how many were copied."""
    target = backup_dir()
    target.mkdir(parents=True, exist_ok=True)
    copied = 0
    for path in notes_dir().glob("*.md"):
        shutil.copy2(path, target / path.name)
        copied += 1
    return copied
