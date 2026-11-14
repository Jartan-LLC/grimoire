"""remindme snooze ID DURATION."""

import re
from datetime import datetime, timedelta
from pathlib import Path

from remindme.store import load, save

_UNITS = {"m": "minutes", "h": "hours", "d": "days"}
_PART = re.compile(r"(\d+)([mhd])")


def _parse_duration(text: str) -> timedelta:
    """A duration such as 10m, 1h30m or 2d."""
    parts = _PART.findall(text)
    if not parts or "".join(n + u for n, u in parts) != text:
        raise ValueError(f"not a duration: {text!r} (try 10m, 1h30m or 2d)")
    return sum((timedelta(**{_UNITS[u]: int(n)}) for n, u in parts), timedelta())


def snooze(path: Path, item_id: int, duration: str, now: datetime) -> None:
    """Make reminder `item_id` due `duration` from now."""
    items = load(path)
    for item in items:
        if item["id"] == item_id:
            item["due"] = (now + _parse_duration(duration)).isoformat(timespec="minutes")
    save(path, items)
