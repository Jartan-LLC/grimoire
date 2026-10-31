# Copyright (c) 2026 The brewkit authors.
"""Bitterness by Tinseth's formula."""

import math

from brewkit.recipe import Recipe


def ibu(recipe: Recipe, gravity: float) -> float:
    """International bitterness units of the recipe's hops."""
    bigness = 1.65 * 0.000125 ** (gravity - 1)
    total = 0.0
    for hop in recipe.hops:
        utilisation = bigness * (1 - math.exp(-0.04 * hop.minutes)) / 4.15
        total += utilisation * hop.alpha / 100 * hop.grams * 1000 / recipe.batch
    return round(total, 1)
