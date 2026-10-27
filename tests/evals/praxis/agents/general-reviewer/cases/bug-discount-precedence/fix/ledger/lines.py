"""Invoice lines."""

from decimal import Decimal

from ledger.money import to_cents


def line_total(unit_price: Decimal, quantity: int, unit_discount: Decimal) -> Decimal:
    """What a line costs: `quantity` units, each `unit_discount` off `unit_price`."""
    return to_cents((unit_price - unit_discount) * quantity)
