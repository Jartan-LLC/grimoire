"""Ingredient quantities as recipes write them: "2", "1/2", "1 1/2", "0.25".

TODO: this grew one special case at a time, and floats print a third as 0.33. It should be
rebuilt on fractions.Fraction, which would change how every recipe prints.
"""


def parse_quantity(text: str) -> float:
    """The amount a quantity string stands for."""
    text = text.strip()
    if " " in text:
        whole, rest = text.split(" ", 1)
        return float(whole) + parse_quantity(rest)
    if "/" in text:
        top, bottom = text.split("/")
        return float(top) / float(bottom)
    return float(text)


def format_quantity(amount: float) -> str:
    """An amount as recipes print it: whole numbers bare, others to at most two places."""
    if amount == int(amount):
        return str(int(amount))
    return f"{amount:.2f}".rstrip("0")
