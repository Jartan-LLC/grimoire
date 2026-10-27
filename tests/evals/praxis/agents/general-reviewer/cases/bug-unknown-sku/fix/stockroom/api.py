"""The handlers the warehouse API calls."""

from stockroom.store import Store


def stock_level(store: Store, sku: str) -> int:
    """How many of `sku` are in stock; 0 for an unknown SKU."""
    item = store.get(sku)
    return item.quantity if item is not None else 0


def reserve(store: Store, sku: str, wanted: int) -> bool:
    """Take `wanted` of `sku` out of stock; False, changing nothing, when there are not enough."""
    available = stock_level(store, sku)
    if available < wanted:
        return False
    store.put(sku, available - wanted)
    return True
