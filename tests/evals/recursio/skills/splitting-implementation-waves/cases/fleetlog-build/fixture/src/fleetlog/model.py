"""The records the fleetlog modules pass to one another."""

import datetime
import enum
from dataclasses import dataclass
from decimal import Decimal


class FleetError(ValueError):
    """Input the fleet tools cannot work with; the message names the vehicle, record or value at fault."""


class FuelKind(enum.Enum):
    """What a vehicle runs on."""

    PETROL = "petrol"
    DIESEL = "diesel"
    ELECTRIC = "electric"


@dataclass(frozen=True)
class Vehicle:
    """A vehicle in the fleet, known by its registration `reg`. `price` is what it cost new."""

    reg: str
    make: str
    fuel: FuelKind
    bought: datetime.date
    price: Decimal


@dataclass(frozen=True)
class FillUp:
    """One visit to the pump. `full` is False for a partial fill that did not top the tank up."""

    reg: str
    day: datetime.date
    odometer_km: int
    litres: Decimal
    cost: Decimal
    full: bool = True


@dataclass(frozen=True)
class ServiceRecord:
    """One piece of maintenance. `kind` is one of "oil", "tyres", "brakes" or "inspection"."""

    reg: str
    day: datetime.date
    odometer_km: int
    kind: str
    cost: Decimal


@dataclass(frozen=True)
class Trip:
    """One logged journey. Times are local, naive datetimes."""

    reg: str
    driver: str
    start: datetime.datetime
    end: datetime.datetime
    start_km: int
    end_km: int
    purpose: str = ""
