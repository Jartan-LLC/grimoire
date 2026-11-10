"""The `habits` command."""

import argparse
from collections import Counter
from datetime import date

from habits import log


def main(argv: list[str] | None = None) -> None:
    """Run one subcommand."""
    parser = argparse.ArgumentParser(prog="habits")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check", help="check in a habit for today")
    check.add_argument("habit")
    sub.add_parser("report", help="count check-ins per habit")
    args = parser.parse_args(argv)

    if args.command == "check":
        log.check_in(args.habit, date.today())
    elif args.command == "report":
        counts = Counter(habit for _, habit in log.entries())
        for habit, count in sorted(counts.items()):
            print(f"{habit:<12} {count}")
