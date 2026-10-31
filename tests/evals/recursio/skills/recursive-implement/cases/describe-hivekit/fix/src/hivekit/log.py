"""Read the inspection log."""

from dataclasses import dataclass
from datetime import date


class LogError(ValueError):
    """A log that cannot be read."""


@dataclass(frozen=True)
class Inspection:
    hive: str
    date: date
    brood: int
    honey: int
    queen: bool
    temper: int


def _number(text: str, low: int, high: int, name: str) -> int:
    value = int(text)
    if not low <= value <= high:
        raise ValueError(f"{name} must be from {low} to {high}")
    return value


def parse_log(text: str) -> list[Inspection]:
    """Every inspection, sorted by hive then date."""
    rows: list[Inspection] = []
    seen: set[tuple[str, date]] = set()
    for number, line in enumerate(text.splitlines(), start=1):
        if number == 1 or not line.strip():
            continue
        fields = [f.strip() for f in line.split(",")]
        try:
            if len(fields) != 6:
                raise ValueError("expected hive,date,brood,honey,queen,temper")
            if fields[4] not in ("yes", "no"):
                raise ValueError("queen must be yes or no")
            row = Inspection(
                fields[0],
                date.fromisoformat(fields[1]),
                _number(fields[2], 0, 10, "brood"),
                _number(fields[3], 0, 10, "honey"),
                fields[4] == "yes",
                _number(fields[5], 1, 5, "temper"),
            )
        except ValueError as error:
            raise LogError(f"line {number}: {error}") from error
        if (row.hive, row.date) in seen:
            raise LogError(f"line {number}: {row.hive} was already inspected on {row.date}")
        seen.add((row.hive, row.date))
        rows.append(row)
    return sorted(rows, key=lambda r: (r.hive, r.date))


def by_hive(log: list[Inspection]) -> dict[str, list[Inspection]]:
    """Each hive's inspections in date order, hives sorted."""
    hives: dict[str, list[Inspection]] = {}
    for row in sorted(log, key=lambda r: (r.hive, r.date)):
        hives.setdefault(row.hive, []).append(row)
    return hives
