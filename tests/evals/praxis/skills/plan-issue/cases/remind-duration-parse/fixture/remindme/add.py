"""remindme add TEXT --in MINUTES."""

from datetime import datetime, timedelta
from pathlib import Path

from remindme.store import load, save


def add_reminder(path: Path, text: str, minutes: int, now: datetime) -> dict:
    """Add a reminder due `minutes` from `now` and return it."""
    items = load(path)
    item = {
        "id": max((i["id"] for i in items), default=0) + 1,
        "text": text,
        "due": (now + timedelta(minutes=minutes)).isoformat(timespec="minutes"),
    }
    save(path, items + [item])
    return item
