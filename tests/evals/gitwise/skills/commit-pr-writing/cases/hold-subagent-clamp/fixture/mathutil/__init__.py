"""Numeric helpers."""


def sign(value: float) -> int:
    """-1, 0 or 1."""
    return (value > 0) - (value < 0)
