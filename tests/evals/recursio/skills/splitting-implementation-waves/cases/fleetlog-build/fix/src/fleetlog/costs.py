"""What a vehicle costs to run: depreciation, fuel and servicing."""

import datetime
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from fleetlog.model import FillUp, FleetError, ServiceRecord, Vehicle

LIFE_DAYS = 2922
RESIDUAL = Decimal("0.1")
CENT = Decimal("0.01")
MILLI = Decimal("0.001")


@dataclass(frozen=True)
class Costs:
    """The cost of running one vehicle over a period. `per_km` is None when no distance was driven."""

    fuel: Decimal
    service: Decimal
    depreciation: Decimal
    total: Decimal
    distance_km: int
    per_km: Decimal | None


def value(vehicle: Vehicle, day: datetime.date) -> Decimal:
    """The vehicle's value on `day`, depreciating in a straight line to 10 % of its price over 2,922 days."""
    age = (day - vehicle.bought).days
    if age < 0:
        raise FleetError(f"vehicle {vehicle.reg}: {day} is before its purchase on {vehicle.bought}")
    share = Decimal(min(age, LIFE_DAYS)) / LIFE_DAYS
    return (vehicle.price - (1 - RESIDUAL) * vehicle.price * share).quantize(CENT, ROUND_HALF_UP)


def running_costs(
    vehicle: Vehicle,
    fillups: list[FillUp],
    services: list[ServiceRecord],
    start: datetime.date,
    end: datetime.date,
) -> Costs:
    """The vehicle's costs from `start` to `end` inclusive, ignoring other vehicles' records."""
    fills = [f for f in fillups if f.reg == vehicle.reg and start <= f.day <= end]
    jobs = [s for s in services if s.reg == vehicle.reg and start <= s.day <= end]
    fuel = sum((f.cost for f in fills), Decimal(0))
    service = sum((s.cost for s in jobs), Decimal(0))
    depreciation = value(vehicle, start) - value(vehicle, end)
    total = fuel + service + depreciation
    readings = [r.odometer_km for r in (*fills, *jobs)]
    distance = max(readings) - min(readings) if len(readings) >= 2 else 0
    per_km = (total / distance).quantize(MILLI, ROUND_HALF_UP) if distance else None
    return Costs(fuel, service, depreciation, total, distance, per_km)
