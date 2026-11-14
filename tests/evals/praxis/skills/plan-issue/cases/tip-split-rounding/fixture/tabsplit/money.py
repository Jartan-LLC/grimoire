"""Amounts are whole cents inside tabsplit."""


def cents(text: str) -> int:
    """`"48.60"` -> 4860."""
    whole, _, frac = text.partition(".")
    return int(whole) * 100 + int((frac + "00")[:2])


def show(amount: int) -> str:
    """4860 -> `"48.60"`."""
    return f"{amount // 100}.{amount % 100:02d}"
