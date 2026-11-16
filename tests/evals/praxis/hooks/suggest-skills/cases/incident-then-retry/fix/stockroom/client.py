"""Prices from the pricing service."""

import time

from stockroom.transport import Timeout, Transport

PRICING_URL = "https://pricing.internal/v1/price/{sku}"
ATTEMPTS = 4
FIRST_WAIT_SECONDS = 0.5


class PriceUnavailable(Exception):
    """The pricing service gave no price for a SKU."""


def fetch_price(sku: str, transport: Transport) -> float:
    """The current unit price of `sku`, in euros, trying again after a timeout or a 503."""
    wait = FIRST_WAIT_SECONDS
    for attempt in range(1, ATTEMPTS + 1):
        try:
            response = transport.get(PRICING_URL.format(sku=sku))
        except Timeout:
            if attempt == ATTEMPTS:
                raise
        else:
            if response.status == 200:
                return response.body["price"]
            if response.status != 503 or attempt == ATTEMPTS:
                raise PriceUnavailable(f"{sku}: pricing answered {response.status}")
        time.sleep(wait)
        wait *= 2
    raise AssertionError("unreachable")
