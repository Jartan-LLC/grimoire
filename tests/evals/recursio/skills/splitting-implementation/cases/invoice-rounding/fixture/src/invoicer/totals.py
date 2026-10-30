"""Invoice totals: each line is printed rounded to the cent."""

from decimal import ROUND_HALF_UP, Decimal

CENT = Decimal("0.01")


def line_total(quantity: int, unit_price: Decimal) -> Decimal:
    """One line's net amount, rounded to the cent as printed."""
    return (quantity * unit_price).quantize(CENT, rounding=ROUND_HALF_UP)


def invoice_total(lines: list[tuple[int, Decimal]], vat_rate: Decimal) -> Decimal:
    """The gross total: the net lines summed, VAT added, rounded to the cent."""
    net = sum((quantity * price for quantity, price in lines), Decimal(0))
    return (net * (1 + vat_rate)).quantize(CENT, rounding=ROUND_HALF_UP)
