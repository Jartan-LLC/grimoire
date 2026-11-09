"""Invoice totals."""

from decimal import Decimal

from billing.money import parse_amount


def total(lines: list[str]) -> Decimal:
    """The sum of the invoice's line amounts."""
    return sum((parse_amount(line) for line in lines), Decimal(0))
