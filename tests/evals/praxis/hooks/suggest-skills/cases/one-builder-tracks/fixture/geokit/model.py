"""The point every reader returns."""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Point:
    """One fix."""

    lat: float
    lon: float
    ele: float | None = None
    time: datetime | None = None
