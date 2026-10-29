"""Members, kept in members.csv: id, name, email."""

import csv
from pathlib import Path


def load(path: Path) -> dict[str, dict[str, str]]:
    """Every member by id."""
    with path.open(newline="") as handle:
        return {row["id"]: row for row in csv.DictReader(handle)}
