"""The records the stationkit modules pass to one another."""

import enum
from dataclasses import dataclass
from datetime import date, datetime

# The measured fields of a Reading, in the order reports list them.
FIELDS = ("temperature_c", "humidity_pct", "pressure_hpa", "wind_ms", "gust_ms", "rain_mm")


@dataclass(frozen=True)
class Reading:
    """One observation in SI units; a field is None when the station did not report it.

    `at` is timezone-aware and in UTC. `rain_mm` is the rain since the station's
    previous reading, not a running total.
    """

    station: str
    at: datetime
    temperature_c: float | None = None
    humidity_pct: float | None = None
    pressure_hpa: float | None = None
    wind_ms: float | None = None
    gust_ms: float | None = None
    rain_mm: float | None = None


class FlagKind(enum.Enum):
    """What a quality-control check found."""

    RANGE = "range"
    STEP = "step"
    FLATLINE = "flatline"
    GAP = "gap"


@dataclass(frozen=True)
class Flag:
    """A quality-control finding on one reading.

    `field` names one of FIELDS, or is None for a finding on the reading as a whole (a gap).
    """

    station: str
    at: datetime
    kind: FlagKind
    field: str | None
    detail: str


@dataclass(frozen=True)
class DailySummary:
    """One station's day in the station's local time.

    A value is None when no unflagged reading of the day carried its field.
    """

    station: str
    day: date
    temperature_min_c: float | None
    temperature_max_c: float | None
    temperature_mean_c: float | None
    gust_max_ms: float | None
    rain_total_mm: float | None
    pressure_mean_hpa: float | None
    coverage_pct: float
    complete: bool
