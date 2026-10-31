# SPDX-License-Identifier: 0BSD
"""The isbntool command."""

import argparse

from isbntool.isbn import is_valid


def main(argv: list[str] | None = None) -> int:
    """Run the isbntool command; return its exit status."""
    parser = argparse.ArgumentParser(prog="isbntool")
    commands = parser.add_subparsers(dest="command", required=True)
    check = commands.add_parser("check")
    check.add_argument("isbns", nargs="+", metavar="ISBN")
    args = parser.parse_args(argv)
    status = 0
    for isbn in args.isbns:
        valid = is_valid(isbn)
        print(f"{isbn} {'valid' if valid else 'invalid'}")
        status = status if valid else 1
    return status
