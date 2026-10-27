"""Fees charged on an invoice."""

from decimal import Decimal

from ledger.money import to_cents

CARD_RATE = Decimal("0.029")
CARD_FIXED = Decimal("0.30")


def card_fee(amount: Decimal) -> Decimal:
    """The card processor's fee on a charge of `amount`."""
    return to_cents(amount * CARD_RATE + CARD_FIXED)
