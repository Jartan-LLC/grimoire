"""Fuel economy: segments between full fills, their average, outliers and cost per km."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from fleetlog.model import FillUp, FleetError


@dataclass(frozen=True)
class Segment:
    """The driving from one full fill (`start_km`) to the next (`end_km`) and the litres it took."""

    start_km: int
    end_km: int
    litres: Decimal
    l_per_100km: Decimal


def _round(value: Decimal, places: str) -> Decimal:
    return value.quantize(Decimal(places), rounding=ROUND_HALF_UP)


def _checked_in_order(fillups):
    """Return the fill-ups sorted by odometer, or raise if they mix vehicles or repeat a reading."""
    regs = sorted({f.reg for f in fillups})
    if len(regs) > 1:
        raise FleetError(f"fill-ups of more than one vehicle: {', '.join(regs)}")
    ordered = sorted(fillups, key=lambda f: f.odometer_km)
    for before, after in zip(ordered, ordered[1:]):
        if before.odometer_km == after.odometer_km:
            raise FleetError(f"vehicle {after.reg} has two fill-ups at odometer {after.odometer_km} km")
    return ordered


def _spans(fillups):
    """Return (start fill, fills counted in the segment) for each segment, in odometer order."""
    spans = []
    start = None
    counted = []
    for fill in _checked_in_order(fillups):
        if start is None:
            if fill.full:
                start = fill
            continue
        counted.append(fill)
        if fill.full:
            spans.append((start, counted))
            start, counted = fill, []
    return spans


def segments(fillups: list[FillUp]) -> list[Segment]:
    """Return one vehicle's segments in odometer order, each from one full fill to the next."""
    result = []
    for start, counted in _spans(fillups):
        litres = sum((f.litres for f in counted), Decimal(0))
        distance = counted[-1].odometer_km - start.odometer_km
        result.append(Segment(start.odometer_km, counted[-1].odometer_km, litres,
                              _round(litres / distance * 100, "0.01")))
    return result


def average(fillups: list[FillUp]) -> Decimal | None:
    """Return total litres over total distance x 100 for all segments, or None without any."""
    segs = segments(fillups)
    if not segs:
        return None
    litres = sum((s.litres for s in segs), Decimal(0))
    distance = sum(s.end_km - s.start_km for s in segs)
    return _round(litres / distance * 100, "0.01")


def _median(values: list[Decimal]) -> Decimal:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return (ordered[middle - 1] + ordered[middle]) / 2


def outliers(segments: list[Segment], tolerance: Decimal = Decimal("0.3")) -> list[Segment]:
    """Return the segments whose l_per_100km is more than `tolerance` (a fraction) from the median."""
    if not segments:
        return []
    median = _median([s.l_per_100km for s in segments])
    return [s for s in segments if abs(s.l_per_100km - median) > tolerance * median]


def cost_per_km(fillups: list[FillUp]) -> Decimal | None:
    """Return the cost of the fills counted in segments over their total distance, or None."""
    spans = _spans(fillups)
    if not spans:
        return None
    cost = sum((f.cost for _, counted in spans for f in counted), Decimal(0))
    distance = sum(counted[-1].odometer_km - start.odometer_km for start, counted in spans)
    return _round(cost / distance, "0.001")
