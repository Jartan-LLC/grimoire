"""Split CSV rows."""

import csv


def split_row(line: str) -> list[str]:
    """The fields of one CSV line."""
    return next(csv.reader([line]))
