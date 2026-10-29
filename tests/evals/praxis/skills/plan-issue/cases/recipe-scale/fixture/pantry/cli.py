"""The `pantry` command."""

import argparse
import os
from pathlib import Path

from pantry import recipe


def recipes_dir() -> Path:
    """Where recipe files live: $PANTRY_DIR, or ./recipes."""
    return Path(os.environ.get("PANTRY_DIR", "recipes"))


def main(argv: list[str] | None = None) -> None:
    """Run one subcommand."""
    parser = argparse.ArgumentParser(prog="pantry")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list the recipes")
    show = sub.add_parser("show", help="print one recipe")
    show.add_argument("name")
    args = parser.parse_args(argv)

    if args.command == "list":
        for path in sorted(recipes_dir().glob("*.txt")):
            print(path.stem)
    elif args.command == "show":
        print(recipe.render(recipe.load(recipes_dir() / f"{args.name}.txt")))
