"""The shelfkit command."""

import argparse
import sys
from datetime import date

from shelfkit.fines import fine
from shelfkit.loans import checkout, return_book
from shelfkit.model import LoanError, load, save
from shelfkit.report import overdue_report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="shelfkit")
    commands = parser.add_subparsers(dest="command", required=True)
    out = commands.add_parser("checkout")
    out.add_argument("library")
    out.add_argument("isbn")
    out.add_argument("member")
    back = commands.add_parser("return")
    back.add_argument("library")
    back.add_argument("isbn")
    commands.add_parser("overdue").add_argument("library")
    for sub in commands.choices.values():
        sub.add_argument("--today", type=date.fromisoformat, default=date.today())
    args = parser.parse_args(argv)
    library = load(args.library)
    try:
        if args.command == "checkout":
            print(f"due {checkout(library, args.isbn, args.member, args.today).due.isoformat()}")
        elif args.command == "return":
            print(f"fine {fine(return_book(library, args.isbn, args.today), args.today):.2f}")
        else:
            for n in overdue_report(library, args.today):
                print(f"{n.member}\t{n.title}\t{n.due.isoformat()}\t{n.days_late}\t{n.fine:.2f}")
            return 0
    except LoanError as error:
        print(f"shelfkit: {error}", file=sys.stderr)
        return 1
    save(library, args.library)
    return 0
