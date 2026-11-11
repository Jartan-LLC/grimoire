"""Prices from the pricing service."""

from stockroom.transport import Transport

PRICING_URL = "https://pricing.internal/v1/price/{sku}"


class PriceUnavailable(Exception):
    """The pricing service gave no price for a SKU."""


def fetch_price(sku: str, transport: Transport) -> float:
    """The current unit price of `sku`, in euros."""
    response = transport.get(PRICING_URL.format(sku=sku))
    if response.status != 200:
        raise PriceUnavailable(f"{sku}: pricing answered {response.status}")
    return response.body["price"]
