from decimal import Decimal

from ledger.fees import card_fee


def test_card_fee_rounds_to_cents() -> None:
    assert card_fee(Decimal("10.00")) == Decimal("0.59")
