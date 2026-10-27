"""The `tally` command."""

import argparse
import pathlib

from tally.report import total


def main(argv: list[str] | None = None) -> int:
    """Print the total of an export file."""
    parser = argparse.ArgumentParser(prog="tally")
    parser.add_argument("export", type=pathlib.Path)
    args = parser.parse_args(argv)
    print(total(args.export.read_text()))
    return 0
