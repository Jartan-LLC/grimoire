"""Trip log checks and monthly mileage."""

from collections import defaultdict
from dataclasses import dataclass

from .model import Trip

MAX_SPEED_KMH = 150
KIND_ORDER = ("times", "odometer", "gap", "overlap", "driver", "speed")


@dataclass(frozen=True)
class Problem:
    """A fault in the trip at index `trip` of the checked list; `kind` is one of `KIND_ORDER`."""

    trip: int
    kind: str
    detail: str


def check(trips: list[Trip]) -> list[Problem]:
    """Return every fault in `trips`, ordered by trip index and then by kind."""
    problems = []
    for i, t in enumerate(trips):
        if t.end <= t.start:
            problems.append(Problem(i, "times", "trip does not end after it starts"))
        if t.end_km < t.start_km:
            problems.append(Problem(i, "odometer", f"end_km {t.end_km} is below start_km {t.start_km}"))
    problems += _vehicle_problems(trips)
    problems += _driver_problems(trips)
    problems += _speed_problems(trips)
    return sorted(problems, key=lambda p: (p.trip, KIND_ORDER.index(p.kind)))


def mileage(trips: list[Trip], year: int, month: int) -> dict[str, int]:
    """Km driven per driver in trips starting in the given month, drivers in sorted order."""
    totals: dict[str, int] = defaultdict(int)
    for t in trips:
        if (t.start.year, t.start.month) == (year, month):
            totals[t.driver] += t.end_km - t.start_km
    return dict(sorted(totals.items()))


def _vehicle_problems(trips: list[Trip]) -> list[Problem]:
    """Gaps and overlaps between consecutive trips of each vehicle."""
    by_vehicle = defaultdict(list)
    for i, t in enumerate(trips):
        by_vehicle[t.reg].append(i)
    problems = []
    for indexes in by_vehicle.values():
        indexes.sort(key=lambda i: trips[i].start)
        for prev_i, i in zip(indexes, indexes[1:]):
            prev, t = trips[prev_i], trips[i]
            if t.start_km != prev.end_km:
                problems.append(Problem(i, "gap", f"gap of {t.start_km - prev.end_km} km"))
            if t.start < prev.end:
                problems.append(Problem(i, "overlap", f"starts before trip {prev_i} ends"))
    return problems


def _driver_problems(trips: list[Trip]) -> list[Problem]:
    """Flag the later-starting of two overlapping trips of one driver in different vehicles."""
    problems = []
    for i, t in enumerate(trips):
        for j, other in enumerate(trips):
            if other.driver != t.driver or other.reg == t.reg:
                continue
            if not (t.start < other.end and other.start < t.end):
                continue
            if (other.start, j) < (t.start, i):
                problems.append(Problem(i, "driver", f"overlaps trip {j} of {other.reg}"))
                break
    return problems


def _speed_problems(trips: list[Trip]) -> list[Problem]:
    """Trips whose average speed exceeds `MAX_SPEED_KMH`; trips with no duration have none."""
    problems = []
    for i, t in enumerate(trips):
        seconds = (t.end - t.start).total_seconds()
        km = t.end_km - t.start_km
        if seconds > 0 and km * 3600 > MAX_SPEED_KMH * seconds:
            problems.append(Problem(i, "speed", f"{km} km in {seconds / 3600:.2f} h"))
    return problems
