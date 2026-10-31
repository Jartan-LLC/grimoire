"""The rotakit command."""

import argparse
import sys
from dataclasses import replace
from datetime import date

from rotakit.ical import to_ical
from rotakit.model import RotaError, load, save
from rotakit.schedule import plan
from rotakit.swaps import swap

__all__ = ["main"]


def main(argv: list[str] | None = None) -> int:
    """Run the rotakit command; return its exit status."""
    parser = argparse.ArgumentParser(prog="rotakit")
    commands = parser.add_subparsers(dest="command", required=True)
    planning = commands.add_parser("plan")
    planning.add_argument("rota")
    planning.add_argument("--from", dest="first", type=date.fromisoformat, required=True)
    planning.add_argument("--weeks", type=int, required=True)
    swapping = commands.add_parser("swap")
    swapping.add_argument("rota")
    swapping.add_argument("weeks", nargs=2, type=date.fromisoformat)
    export = commands.add_parser("export")
    export.add_argument("rota")
    export.add_argument("--person")
    args = parser.parse_args(argv)
    try:
        rota = load(args.rota)
        if args.command == "plan":
            rota = replace(rota, weeks=plan(rota.people, args.first, args.weeks))
            names = {p.id: p.name for p in rota.people}
            save(rota, args.rota)
            for week in rota.weeks:
                print(f"{week.start.isoformat()} {names[week.person]}")
        elif args.command == "swap":
            first, second = args.weeks
            save(swap(rota, first, second), args.rota)
            print(f"swapped {first.isoformat()} and {second.isoformat()}")
        else:
            sys.stdout.write(to_ical(rota, args.person))
    except RotaError as error:
        print(f"rotakit: {error}", file=sys.stderr)
        return 1
    return 0
