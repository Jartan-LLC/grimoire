"""The handlers the warehouse API calls."""

from stockroom.store import Store


def stock_level(store: Store, sku: str) -> int:
    """How many of `sku` are in stock; 0 for an unknown SKU."""
    item = store.get(sku)
    return item.quantity if item is not None else 0
