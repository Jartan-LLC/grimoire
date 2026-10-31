# Copyright (c) 2026 The brewkit authors.
"""Gravity and alcohol."""

from brewkit.recipe import Recipe


def original_gravity(recipe: Recipe) -> float:
    """The wort's gravity before fermentation."""
    points = sum(g.kg * g.potential * recipe.efficiency / 100 for g in recipe.grains)
    return round(1 + points / recipe.batch / 1000, 3)


def final_gravity(og: float, attenuation: float) -> float:
    """The gravity once the yeast has eaten its share."""
    return round(1 + (og - 1) * (1 - attenuation / 100), 3)


def abv(og: float, fg: float) -> float:
    """Alcohol by volume, in percent, by the simple formula."""
    return round((og - fg) * 131.25, 1)
