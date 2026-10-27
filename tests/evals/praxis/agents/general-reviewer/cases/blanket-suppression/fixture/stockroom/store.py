"""An in-memory store of items, keyed by SKU."""

from datetime import UTC, datetime

from stockroom.models import Item


class Store:
    """Items by SKU."""

    def __init__(self) -> None:
        """An empty store."""
        self._items: dict[str, Item] = {}

    def put(self, sku: str, quantity: int) -> Item:
        """Set the quantity of `sku`."""
        item = Item(sku, quantity, datetime.now(UTC))
        self._items[sku] = item
        return item

    def get(self, sku: str) -> Item | None:
        """The item for `sku`, or None when it is not stocked."""
        return self._items.get(sku)
