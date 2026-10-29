"""Count, mean, min and max per column."""

import csv
from pathlib import Path


def numeric_columns(path: Path, sep: str = ",") -> dict[str, list[float]]:
    """The values of every column whose non-empty cells are all numbers."""
    with path.open(newline="") as handle:
        rows = list(csv.DictReader(handle, delimiter=sep))
    columns: dict[str, list[float]] = {}
    for name in rows[0] if rows else []:
        cells = [row[name].strip() for row in rows if row[name].strip()]
        try:
            columns[name] = [float(cell) for cell in cells]
        except ValueError:
            continue
    return columns


def summary(values: list[float]) -> dict[str, float]:
    """Count, mean, min and max of `values`."""
    return {"count": len(values), "mean": sum(values) / len(values), "min": min(values), "max": max(values)}
