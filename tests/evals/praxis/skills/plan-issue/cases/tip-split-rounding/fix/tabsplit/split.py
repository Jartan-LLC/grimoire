"""Shares of a bill."""


def split(total: int, people: int) -> list[int]:
    """Each person's share of `total` cents; the shares add up to `total`."""
    base, extra = divmod(total, people)
    return [base + 1] * extra + [base] * (people - extra)
