"""The command line: python3 -m csvstats FILE [--col NAME] [--sep CHAR]."""

import argparse
from pathlib import Path

from csvstats.stats import numeric_columns, summary


def build_parser() -> argparse.ArgumentParser:
    """The argument parser."""
    parser = argparse.ArgumentParser(prog="csvstats")
    parser.add_argument("file", type=Path)
    parser.add_argument("--col", help="summarise only this column")
    parser.add_argument("--sep", default=",", help="the field separator (default ,)")
    return parser


def main(argv: list[str] | None = None) -> None:
    """Print one summary line per numeric column."""
    args = build_parser().parse_args(argv)
    columns = numeric_columns(args.file, args.sep)
    for name, values in columns.items():
        if args.col in (None, name) and values:
            s = summary(values)
            print(f"{name}: count {s['count']}  mean {s['mean']:.2f}  min {s['min']:g}  max {s['max']:g}")
