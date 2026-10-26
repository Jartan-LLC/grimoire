"""Parse ISO dates."""

from datetime import date


def parse_date(text: str) -> date:
    """The date in `text` (YYYY-MM-DD); ValueError for a date that does not exist."""
    year, month, day = (int(part) for part in text.split("-"))
    return date(year, month, day)
