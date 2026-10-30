"""The tabkit command."""

import argparse

from .table import load


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="tabkit")
    sub = parser.add_subparsers(dest="command", required=True)
    head = sub.add_parser("head")
    head.add_argument("file")
    head.add_argument("-n", type=int, default=5)
    args = parser.parse_args(argv)
    table = load(args.file)
    print(",".join(table.columns))
    for row in table.rows[: args.n]:
        print(",".join(row[c] for c in table.columns))
    return 0
