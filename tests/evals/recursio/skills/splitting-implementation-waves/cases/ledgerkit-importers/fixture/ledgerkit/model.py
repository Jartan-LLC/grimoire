"""Shared types for every ledgerkit module."""

from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Transaction:
    """One booked transaction. `amount` is negative for money out."""

    day: date
    amount: Decimal
    payee: str
    memo: str = ""
    category: str | None = None
    ref: str | None = None
    currency: str = "EUR"


@dataclass(frozen=True)
class Skipped:
    """A record left out of an import: the 1-based line it starts on and why."""

    line: int
    reason: str


@dataclass
class ImportResult:
    """What an importer hands back: the good transactions and the records it skipped."""

    transactions: list[Transaction] = field(default_factory=list)
    skipped: list[Skipped] = field(default_factory=list)


class FormatError(Exception):
    """The input is not in the importer's format, or is broken beyond one record."""
