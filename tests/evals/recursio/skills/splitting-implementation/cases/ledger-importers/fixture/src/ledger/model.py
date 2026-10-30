"""The record every importer produces."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Transaction:
    """One booked movement on an account; `amount` is negative for money going out."""

    booked: date
    amount: Decimal
    payee: str
    memo: str = ""
    account: str = ""
