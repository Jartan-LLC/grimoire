"""Totals per ISO week from rows of date (YYYY-MM-DD), project and hours."""

import csv
from collections import defaultdict
from datetime import date
from pathlib import Path

from timesheet.hours import parse_hours


def weekly_totals(rows: list[dict[str, str]]) -> dict[str, float]:
    """Total hours per week, keyed "2026-W43"."""
    totals: dict[str, float] = defaultdict(float)
    for row in rows:
        year, week, _ = date.fromisoformat(row["date"]).isocalendar()
        totals[f"{year}-W{week:02d}"] += parse_hours(row["hours"])
    return dict(totals)


def read_sheet(path: Path) -> list[dict[str, str]]:
    """The rows of a timesheet CSV."""
    with path.open(newline="") as handle:
        return list(csv.DictReader(handle))
