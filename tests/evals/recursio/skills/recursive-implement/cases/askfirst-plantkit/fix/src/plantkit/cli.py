"""The plantkit command."""

import argparse
import sys
from datetime import date
from pathlib import Path

from plantkit.companions import conflicts
from plantkit.model import GardenError, load_garden
from plantkit.rain import parse_rain
from plantkit.sowing import sow_dates
from plantkit.watering import weekly_water


def main(argv: list[str] | None = None) -> int:
    """Run the plantkit command; return its exit status."""
    parser = argparse.ArgumentParser(prog="plantkit")
    commands = parser.add_subparsers(dest="command", required=True)
    sow = commands.add_parser("sow")
    sow.add_argument("garden")
    # --out stays until the maintainer agrees to drop it.
    sow.add_argument("--output", "--out", dest="output", metavar="FILE")
    water = commands.add_parser("water")
    water.add_argument("garden")
    water.add_argument("rain")
    water.add_argument("--week", type=date.fromisoformat, required=True)
    water.add_argument("--output", metavar="FILE")
    check = commands.add_parser("check")
    check.add_argument("garden")
    check.add_argument("--output", metavar="FILE")
    args = parser.parse_args(argv)
    status = 0
    try:
        garden = load_garden(args.garden)
        if args.command == "sow":
            text = "".join(f"{day.isoformat()} {name}\n" for day, name in sow_dates(garden))
        elif args.command == "water":
            need = weekly_water(garden, parse_rain(Path(args.rain).read_text()), args.week)
            text = "".join(f"{bed} {mm:.1f}\n" for bed, mm in need.items())
        else:
            found = conflicts(garden)
            text = "".join(f"{bed}: {a} + {b}\n" for bed, a, b in found)
            status = 1 if found else 0
    except (GardenError, OSError) as error:
        print(f"plantkit: {error}", file=sys.stderr)
        return 2
    if args.output:
        Path(args.output).write_text(text)
    else:
        sys.stdout.write(text)
    return status
