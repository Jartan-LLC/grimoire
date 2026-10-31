# SPDX-License-Identifier: MIT
"""Bill usage intervals against a time-of-use tariff."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from meterkit.readings import Interval


@dataclass(frozen=True)
class Tariff:
    peak: Decimal
    offpeak: Decimal
    standing: Decimal


@dataclass(frozen=True)
class Bill:
    peak_kwh: Decimal
    offpeak_kwh: Decimal
    days: int
    total: Decimal


def bill(intervals: list[Interval], tariff: Tariff) -> Bill:
    peak = sum((i.kwh for i in intervals if 7 <= i.start.hour <= 22), Decimal(0))
    offpeak = sum((i.kwh for i in intervals if not 7 <= i.start.hour <= 22), Decimal(0))
    days = len({i.start.date() for i in intervals})
    total = peak * tariff.peak + offpeak * tariff.offpeak + days * tariff.standing
    return Bill(peak, offpeak, days, total.quantize(Decimal("0.01"), ROUND_HALF_UP))
