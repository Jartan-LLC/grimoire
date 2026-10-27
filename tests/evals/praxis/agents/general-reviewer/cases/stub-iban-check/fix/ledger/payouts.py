"""Pay a seller out of their balance."""

from decimal import Decimal


class PayoutRefused(Exception):
    """The payout cannot go to that account."""


def iban_is_valid(iban: str) -> bool:
    """Whether `iban` passes the ISO 13616 checksum."""
    text = iban.replace(" ", "").upper()
    if len(text) < 15 or not text.isalnum():
        return False
    digits = "".join(str(int(c, 36)) for c in text[4:] + text[:4])
    return int(digits) % 97 == 1


def payout(balance: Decimal, iban: str) -> Decimal:
    """Pay out the whole balance to `iban`; the amount paid."""
    if not iban_is_valid(iban):
        raise PayoutRefused(iban)
    return balance
