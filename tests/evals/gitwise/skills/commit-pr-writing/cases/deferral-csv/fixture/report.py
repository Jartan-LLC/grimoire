"""Print the sales report."""

import argparse

ROWS = [("north", 12), ("south", 7)]


def table(rows: list[tuple[str, int]]) -> str:
    """The rows as an aligned text table."""
    return "\n".join(f"{name:<8}{units:>4}" for name, units in rows)


def main(argv: list[str] | None = None) -> str:
    """The report text for the command line `argv`."""
    argparse.ArgumentParser().parse_args(argv)
    return table(ROWS)
