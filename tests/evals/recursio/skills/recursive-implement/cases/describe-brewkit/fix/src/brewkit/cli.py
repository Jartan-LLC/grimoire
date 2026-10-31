# Copyright (c) 2026 The brewkit authors.
"""The brewkit command."""

import argparse
import sys
from dataclasses import replace
from pathlib import Path

from brewkit.bitterness import ibu
from brewkit.colour import describe, srm
from brewkit.gravity import abv, final_gravity, original_gravity
from brewkit.recipe import RecipeError, format_recipe, parse_recipe


def main(argv: list[str] | None = None) -> int:
    """Run the brewkit command; return its exit status."""
    parser = argparse.ArgumentParser(prog="brewkit")
    commands = parser.add_subparsers(dest="command", required=True)
    stats = commands.add_parser("stats")
    stats.add_argument("recipe")
    stats.add_argument("--attenuation", type=float, default=75)
    scale = commands.add_parser("scale")
    scale.add_argument("recipe")
    scale.add_argument("--batch", type=float, required=True)
    args = parser.parse_args(argv)
    try:
        recipe = parse_recipe(Path(args.recipe).read_text())
    except (OSError, RecipeError) as error:
        print(f"brewkit: {error}", file=sys.stderr)
        return 2
    if args.command == "stats":
        og = original_gravity(recipe)
        fg = final_gravity(og, args.attenuation)
        colour = srm(recipe)
        print(f"og: {og:.3f}\nfg: {fg:.3f}\nabv: {abv(og, fg):.1f}%")
        print(f"ibu: {ibu(recipe, og):.1f}\nsrm: {colour:.1f} ({describe(colour)})")
    else:
        factor = args.batch / recipe.batch
        scaled = replace(
            recipe,
            batch=args.batch,
            grains=[replace(g, kg=g.kg * factor) for g in recipe.grains],
            hops=[replace(h, grams=h.grams * factor) for h in recipe.hops],
        )
        sys.stdout.write(format_recipe(scaled))
    return 0
