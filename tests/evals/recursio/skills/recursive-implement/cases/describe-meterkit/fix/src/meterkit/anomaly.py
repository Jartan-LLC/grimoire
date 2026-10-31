# SPDX-License-Identifier: MIT
"""Find intervals far above their meter's median usage."""

import statistics
from dataclasses import dataclass
from decimal import Decimal

from meterkit.readings import Interval


@dataclass(frozen=True)
class Anomaly:
    interval: Interval
    median: Decimal


def anomalies(intervals: list[Interval], factor: Decimal = Decimal(3)) -> list[Anomaly]:
    by_meter: dict[str, list[Decimal]] = {}
    for interval in intervals:
        by_meter.setdefault(interval.meter, []).append(interval.kwh)
    medians = {m: statistics.median(k) for m, k in by_meter.items() if len(k) >= 3}
    return [
        Anomaly(i, medians[i.meter])
        for i in intervals
        if i.meter in medians and i.kwh > factor * medians[i.meter]
    ]
