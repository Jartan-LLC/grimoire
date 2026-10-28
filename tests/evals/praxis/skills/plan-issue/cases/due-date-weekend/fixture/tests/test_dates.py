from datetime import date

from invoicer.dates import due_date


def test_weekday_due_date_is_kept():
    # Friday 6 March 2026 + 14 days is Friday 20 March.
    assert due_date(date(2026, 3, 6), 14) == date(2026, 3, 20)


def test_sunday_moves_to_monday():
    # Sunday 1 March 2026 + 14 days is Sunday 15 March.
    assert due_date(date(2026, 3, 1), 14) == date(2026, 3, 16)
