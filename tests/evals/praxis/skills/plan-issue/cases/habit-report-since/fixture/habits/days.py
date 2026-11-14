"""Days as the log writes them: "2026-10-03".

TODO: parse_day was written before we used date.fromisoformat anywhere. Switching to it
would change the message every command prints for a bad date, so it needs its own change.
"""

from datetime import date


def parse_day(text: str) -> date:
    """The day a "YYYY-MM-DD" string names."""
    parts = text.strip().split("-")
    if len(parts) != 3 or not all(p.isdigit() for p in parts):
        raise ValueError(f"not a day: {text!r} (want YYYY-MM-DD)")
    year, month, day = (int(p) for p in parts)
    return date(year, month, day)


def format_day(day: date) -> str:
    """A day as the log writes it."""
    return f"{day.year:04d}-{day.month:02d}-{day.day:02d}"
