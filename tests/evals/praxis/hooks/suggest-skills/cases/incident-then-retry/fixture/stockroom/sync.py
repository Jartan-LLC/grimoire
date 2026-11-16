"""The nightly price sync: refresh the stored price of every SKU."""

from stockroom.client import fetch_price
from stockroom.transport import Transport


def sync_prices(skus: list[str], transport: Transport, store: dict[str, float]) -> None:
    """Store the current price of each SKU in `skus`."""
    for sku in skus:
        store[sku] = fetch_price(sku, transport)
