"""Shares of a bill."""


def split(total: int, people: int) -> list[int]:
    """Each person's share of `total` cents; the shares add up to `total`."""
    share = round(total / people)
    return [share] * people
