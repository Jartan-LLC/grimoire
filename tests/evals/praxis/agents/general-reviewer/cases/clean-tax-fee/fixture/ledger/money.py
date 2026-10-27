"""Amounts of money, held as Decimal so cents never drift."""

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def to_cents(amount: Decimal) -> Decimal:
    """`amount` rounded half-up to whole cents."""
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)
