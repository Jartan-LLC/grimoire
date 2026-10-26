"""Format amounts of money."""


def money(amount: float) -> str:
    """`amount` as dollars, two decimals, the sign before the dollar sign."""
    sign = "-" if amount < 0 else ""
    return f"{sign}${abs(amount):.2f}"
