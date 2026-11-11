"""Report lines for the end of day."""

from tills.totals import total_cents


def end_of_day(amounts: list[int]) -> str:
    """The day's total."""
    return f"total {total_cents(amounts) / 100:.2f}"
