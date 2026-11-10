"""Calendar helpers."""


def days_in_year(leap: bool) -> int:
    """366 in a leap year, else 365."""
    return 366 if leap else 365
