"""Sales totals."""


def legacy_total(amounts: list[float]) -> float:
    """The old float total, kept for the 2024 reports."""
    return round(sum(amounts), 2)


def total_cents(amounts: list[int]) -> int:
    """The total in cents."""
    return sum(amounts)
