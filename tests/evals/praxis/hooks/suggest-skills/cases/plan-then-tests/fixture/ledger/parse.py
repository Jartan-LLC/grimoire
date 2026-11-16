"""Parse one line of a bank statement export: `date;payee;amount currency`."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

# Digits after the decimal point each currency allows.
MINOR_UNITS = {"EUR": 2, "USD": 2, "JPY": 0}


class ParseError(ValueError):
    """A line that is not a statement entry."""


@dataclass(frozen=True)
class Entry:
    """One statement entry."""

    day: date
    payee: str
    amount: Decimal
    currency: str


def parse_line(line: str) -> Entry:
    """The entry on `line`, such as `2026-03-01;Coffee Corner;-3.50 EUR`."""
    fields = line.strip().split(";")
    if len(fields) != 3:
        raise ParseError(f"expected 3 fields, got {len(fields)}: {line!r}")
    day_text, payee, money = fields
    try:
        day = date.fromisoformat(day_text)
    except ValueError as error:
        raise ParseError(f"bad date {day_text!r}") from error
    amount_text, _, currency = money.partition(" ")
    if currency not in MINOR_UNITS:
        raise ParseError(f"unknown currency {currency!r}")
    try:
        amount = Decimal(amount_text)
    except InvalidOperation as error:
        raise ParseError(f"bad amount {amount_text!r}") from error
    exponent = amount.as_tuple().exponent
    if isinstance(exponent, int) and -exponent > MINOR_UNITS[currency]:
        raise ParseError(f"{currency} takes {MINOR_UNITS[currency]} decimals: {amount_text!r}")
    if not payee.strip():
        raise ParseError("empty payee")
    return Entry(day, payee.strip(), amount, currency)
