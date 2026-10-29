"""Invoice due dates."""

from datetime import date, timedelta

SATURDAY = 5
SUNDAY = 6


def due_date(issued: date, terms_days: int) -> date:
    """The day an invoice falls due: `terms_days` after `issued`, moved off a weekend."""
    due = issued + timedelta(days=terms_days)
    if due.weekday() == SATURDAY:
        due += timedelta(days=2)
    elif due.weekday() == SUNDAY:
        due += timedelta(days=1)
    return due
