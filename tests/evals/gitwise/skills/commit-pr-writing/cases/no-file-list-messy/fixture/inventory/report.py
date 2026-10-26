from inventory import get_qty


def line(stock: dict[str, int], sku: str) -> str:
    """One report line."""
    return f"{sku}: {get_qty(stock, sku)}"
