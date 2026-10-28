"""Exchange rates from the rates API."""

import json
import os
import urllib.request
from decimal import ROUND_HALF_EVEN, Decimal

RATES_URL = os.environ.get("FX_RATES_URL", "https://rates.example.org/latest")


def fetch_rates(base: str) -> dict[str, Decimal]:
    """Today's rates from `base` to every other currency the API knows."""
    with urllib.request.urlopen(f"{RATES_URL}?base={base}", timeout=10) as response:
        body = json.load(response)
    return {code: Decimal(str(rate)) for code, rate in body["rates"].items()}


def convert(amount: Decimal, rate: Decimal) -> Decimal:
    """`amount` at `rate`, rounded to cents the way the till rounds."""
    return (amount * rate).quantize(Decimal("0.01"), rounding=ROUND_HALF_EVEN)
