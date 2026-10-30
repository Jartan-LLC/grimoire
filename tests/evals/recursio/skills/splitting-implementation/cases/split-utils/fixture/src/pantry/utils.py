"""Helpers."""

import re
from datetime import date, datetime

GRAMS = {"g": 1, "kg": 1000, "oz": 28.3495, "lb": 453.592}
MILLILITRES = {"ml": 1, "l": 1000, "cup": 236.588, "tbsp": 14.787, "tsp": 4.929}


def to_grams(amount: float, unit: str) -> float:
    """`amount` of `unit` in grams."""
    return amount * GRAMS[unit.lower()]


def to_millilitres(amount: float, unit: str) -> float:
    """`amount` of `unit` in millilitres."""
    return amount * MILLILITRES[unit.lower()]


def is_weight(unit: str) -> bool:
    return unit.lower() in GRAMS


def parse_best_before(text: str) -> date:
    """A best-before date written as dd/mm/yyyy or yyyy-mm-dd."""
    if re.fullmatch(r"\d{2}/\d{2}/\d{4}", text):
        return datetime.strptime(text, "%d/%m/%Y").date()
    return date.fromisoformat(text)


def days_left(best_before: date, today: date) -> int:
    """Days until `best_before`; negative once it has passed."""
    return (best_before - today).days


def is_expired(best_before: date, today: date) -> bool:
    return days_left(best_before, today) < 0


def item_title(name: str) -> str:
    """`name` in title case, keeping short words lower case after the first."""
    small = {"and", "of", "in", "with"}
    words = name.split()
    return " ".join(w if i and w in small else w.capitalize() for i, w in enumerate(words))


def pluralise(word: str, count: int) -> str:
    if count == 1:
        return word
    if word.endswith(("s", "x", "ch", "sh")):
        return word + "es"
    return word + "s"


def format_quantity(amount: float, unit: str) -> str:
    """`amount` and `unit` for a shopping list: whole numbers without decimals."""
    shown = f"{amount:g}"
    return f"{shown} {pluralise(unit, 1 if amount == 1 else 2)}"
