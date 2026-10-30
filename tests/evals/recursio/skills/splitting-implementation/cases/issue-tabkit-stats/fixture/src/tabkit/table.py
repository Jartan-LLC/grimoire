"""A CSV file as a list of columns and rows."""

import csv
from dataclasses import dataclass


@dataclass
class Table:
    columns: list[str]
    rows: list[dict[str, str]]


def load(path: str) -> Table:
    """Read `path` as CSV with a header row."""
    with open(path, newline="") as handle:
        reader = csv.DictReader(handle)
        rows = list(reader)
    return Table(list(reader.fieldnames or []), rows)
