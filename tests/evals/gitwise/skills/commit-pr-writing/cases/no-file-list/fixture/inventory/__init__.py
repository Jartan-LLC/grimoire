"""Stock levels."""


def get_qty(stock: dict[str, int], sku: str) -> int:
    """Units of `sku` in stock; 0 when unknown."""
    return stock.get(sku, 0)
