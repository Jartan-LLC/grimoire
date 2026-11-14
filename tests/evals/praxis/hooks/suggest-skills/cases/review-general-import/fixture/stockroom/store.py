"""An in-memory store of stock levels, keyed by SKU."""


class Store:
    """Stock levels by SKU."""

    def __init__(self) -> None:
        """An empty store."""
        self._levels: dict[str, int] = {}

    def put(self, sku: str, quantity: int) -> None:
        """Set the quantity of `sku`."""
        if quantity < 0:
            raise ValueError(f"{sku}: negative quantity {quantity}")
        self._levels[sku] = quantity

    def get(self, sku: str) -> int:
        """The quantity of `sku`, 0 when it is not stocked."""
        return self._levels.get(sku, 0)
