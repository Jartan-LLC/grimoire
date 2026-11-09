"""Stock records."""


def total(items: dict[str, int]) -> int:
    """Units in stock across all items."""
    return sum(items.values())
