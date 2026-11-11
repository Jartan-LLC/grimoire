"""The monthly report. Amounts arrive already parsed (see parse_amount)."""

from decimal import Decimal


def line(name: str, amount: Decimal) -> str:
    """One report line."""
    return f"{name:<30}{amount:>12.2f}"
