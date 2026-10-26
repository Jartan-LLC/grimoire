"""Parse ISO dates."""

from datetime import date, timedelta


def parse_date(text: str) -> date:
    """The date in `text` (YYYY-MM-DD); days past the month's end roll over."""
    year, month, day = (int(part) for part in text.split("-"))
    return date(year, month, 1) + timedelta(days=day - 1)
