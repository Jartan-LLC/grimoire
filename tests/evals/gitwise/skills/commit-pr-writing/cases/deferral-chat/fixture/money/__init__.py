"""Format amounts of money."""


def money(amount: float) -> str:
    """`amount` as dollars, two decimals."""
    return f"${amount:.2f}"
