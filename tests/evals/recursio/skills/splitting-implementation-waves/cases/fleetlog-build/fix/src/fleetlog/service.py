"""The service schedule: what each vehicle is due for, and how urgent it is."""

import calendar
import datetime
from dataclasses import dataclass

from .model import FleetError, FuelKind, ServiceRecord, Vehicle

DUE_SOON_DAYS = 30
DUE_SOON_KM = 1000


@dataclass(frozen=True)
class Item:
    """One scheduled item. `first_months` replaces `months` for the first one after purchase."""

    kind: str
    km: int | None = None
    months: int | None = None
    first_months: int | None = None


SCHEDULE = (
    Item("oil", km=15000, months=12),
    Item("tyres", km=10000),
    Item("brakes", months=24),
    Item("inspection", months=24, first_months=36),
)


@dataclass(frozen=True)
class Due:
    """What a vehicle is due for. `due_day` or `due_km` is None when the item is not counted that way."""

    kind: str
    due_day: datetime.date | None
    due_km: int | None
    status: str


_STATUS_ORDER = {"overdue": 0, "due-soon": 1, "ok": 2}


def _add_months(day: datetime.date, months: int) -> datetime.date:
    """`day` plus `months`, clamped to the last day of a shorter month."""
    index = day.year * 12 + day.month - 1 + months
    year, month = divmod(index, 12)
    month += 1
    return day.replace(
        year=year, month=month, day=min(day.day, calendar.monthrange(year, month)[1])
    )


def _status(item_due_day, due_km, today, odometer_km) -> str:
    if (item_due_day is not None and today >= item_due_day) or (
        due_km is not None and odometer_km >= due_km
    ):
        return "overdue"
    if (
        item_due_day is not None and (item_due_day - today).days <= DUE_SOON_DAYS
    ) or (due_km is not None and due_km - odometer_km <= DUE_SOON_KM):
        return "due-soon"
    return "ok"


def _latest_by_kind(
    vehicle: Vehicle, records: list[ServiceRecord], today: datetime.date
) -> dict[str, ServiceRecord]:
    kinds = {item.kind for item in SCHEDULE}
    latest: dict[str, ServiceRecord] = {}
    for record in records:
        if record.reg != vehicle.reg:
            continue
        if record.kind not in kinds:
            raise FleetError(
                f"service record for {vehicle.reg} on {record.day} has unknown kind {record.kind!r}"
            )
        if record.day > today:
            raise FleetError(
                f"{record.kind} record for {vehicle.reg} is dated {record.day}, after today ({today})"
            )
        if record.kind not in latest or record.day > latest[record.kind].day:
            latest[record.kind] = record
    return latest


def due(
    vehicle: Vehicle,
    records: list[ServiceRecord],
    today: datetime.date,
    odometer_km: int,
) -> list[Due]:
    """Each scheduled item for `vehicle`, ordered overdue, due-soon, ok, then by `SCHEDULE`."""
    latest = _latest_by_kind(vehicle, records, today)
    result = []
    for item in SCHEDULE:
        if item.kind == "oil" and vehicle.fuel is FuelKind.ELECTRIC:
            continue
        record = latest.get(item.kind)
        base_day = record.day if record else vehicle.bought
        base_km = record.odometer_km if record else 0
        months = item.months if record or item.first_months is None else item.first_months
        due_day = None if months is None else _add_months(base_day, months)
        due_km = None if item.km is None else base_km + item.km
        result.append(Due(item.kind, due_day, due_km, _status(due_day, due_km, today, odometer_km)))
    return sorted(result, key=lambda d: _STATUS_ORDER[d.status])
