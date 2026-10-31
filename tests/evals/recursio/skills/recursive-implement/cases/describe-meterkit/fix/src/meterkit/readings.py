# SPDX-License-Identifier: MIT
"""Parse meter readings and turn them into usage intervals."""

import csv
import io
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation

ROLLOVER = Decimal(100000)


class ReadingError(ValueError):
    """Bad input."""


@dataclass(frozen=True)
class Reading:
    meter: str
    time: datetime
    register: Decimal


@dataclass(frozen=True)
class Interval:
    meter: str
    start: datetime
    end: datetime
    kwh: Decimal


def parse_readings(text: str) -> list[Reading]:
    rows = list(csv.reader(io.StringIO(text)))
    readings = []
    for number, row in enumerate(rows[1:], start=2):
        if not row:
            continue
        if len(row) != 3:
            raise ReadingError(f"line {number}: expected 3 fields, got {len(row)}")
        meter, time, register = row
        try:
            when = datetime.strptime(time, "%Y-%m-%dT%H:%M")
            value = Decimal(register)
        except (ValueError, InvalidOperation):
            raise ReadingError(f"line {number}: cannot parse {time!r} or {register!r}") from None
        if value < 0:
            raise ReadingError(f"line {number}: negative register {register}")
        readings.append(Reading(meter, when, value))
    return readings


def intervals(readings: list[Reading]) -> list[Interval]:
    by_meter: dict[str, list[Reading]] = {}
    for reading in readings:
        by_meter.setdefault(reading.meter, []).append(reading)
    result = []
    for meter in sorted(by_meter):
        ordered = sorted(by_meter[meter], key=lambda r: r.time)
        for earlier, later in zip(ordered, ordered[1:]):
            if earlier.time == later.time:
                raise ReadingError(f"meter {meter} has two readings at {later.time:%Y-%m-%dT%H:%M}")
            kwh = later.register - earlier.register
            if kwh < 0:
                kwh += ROLLOVER
            result.append(Interval(meter, earlier.time, later.time, kwh))
    return result
