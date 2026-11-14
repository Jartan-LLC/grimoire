"""Amounts of money as the accounting system writes them."""

from decimal import Decimal


def parse_amount(text: str) -> Decimal:
    """`1.234,56` or `1234.56` as a Decimal."""
    if "," in text:
        text = text.replace(".", "").replace(",", ".")
    return Decimal(text)
