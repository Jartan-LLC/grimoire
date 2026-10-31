# Copyright (c) 2026 The brewkit authors.
"""Colour by Morey's formula."""

from brewkit.recipe import Recipe

NAMES = ((4, "straw"), (8, "gold"), (15, "amber"), (25, "brown"))


def srm(recipe: Recipe) -> float:
    """The beer's colour in SRM."""
    mcu = sum(g.colour * g.kg * 2.2046 for g in recipe.grains) / (recipe.batch * 0.2642)
    return round(1.4922 * mcu**0.6859, 1)


def describe(value: float) -> str:
    """A word for an SRM colour."""
    return next((name for limit, name in NAMES if value < limit), "black")
