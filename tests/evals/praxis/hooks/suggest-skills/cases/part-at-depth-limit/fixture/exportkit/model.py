"""The record every format writes."""

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Record:
    """One exported row."""

    id: int
    name: str
    amount: Decimal
