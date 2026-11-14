"""Refunds against an invoice."""

from decimal import Decimal

from billing import money


def refund(paid: str, kept: Decimal) -> Decimal:
    """What goes back to the customer."""
    return money.parse_amount(paid) - kept
