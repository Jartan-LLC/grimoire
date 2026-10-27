"""Turn rows into totals."""

from decimal import Decimal

from tally.rows import parse_rows


def total(text: str, column: str = "amount") -> Decimal:
    """The sum of `column` over the export's rows."""
    return sum((Decimal(row[column]) for row in parse_rows(text)), Decimal(0))
