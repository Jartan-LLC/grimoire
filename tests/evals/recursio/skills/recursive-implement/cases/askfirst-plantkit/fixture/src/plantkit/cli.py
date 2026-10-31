"""The plantkit command."""

import argparse
import sys
from pathlib import Path

from plantkit.model import GardenError, load_garden
from plantkit.sowing import sow_dates


def main(argv: list[str] | None = None) -> int:
    """Run the plantkit command; return its exit status."""
    parser = argparse.ArgumentParser(prog="plantkit")
    commands = parser.add_subparsers(dest="command", required=True)
    sow = commands.add_parser("sow")
    sow.add_argument("garden")
    sow.add_argument("--out", metavar="FILE")
    args = parser.parse_args(argv)
    try:
        garden = load_garden(args.garden)
    except (GardenError, OSError) as error:
        print(f"plantkit: {error}", file=sys.stderr)
        return 2
    text = "".join(f"{day.isoformat()} {name}\n" for day, name in sow_dates(garden))
    if args.out:
        Path(args.out).write_text(text)
    else:
        sys.stdout.write(text)
    return 0
