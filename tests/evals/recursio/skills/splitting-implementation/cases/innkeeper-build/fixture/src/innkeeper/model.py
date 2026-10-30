"""The records the innkeeper modules pass to one another.

Money is always a Decimal in the hotel's currency, never a float.
"""

import enum
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal

# The smallest amount of money; every charge is rounded to it.
CENTS = Decimal("0.01")


@dataclass(frozen=True)
class RoomType:
    """A kind of room. `base_occupancy` adults are included in the rate; more pay a surcharge."""

    code: str
    name: str
    base_occupancy: int
    max_adults: int
    max_occupancy: int


@dataclass(frozen=True)
class Room:
    """One physical room. Room numbers are strings such as "101" or "12A"."""

    number: str
    room_type: str
    floor: int
    out_of_order: bool = False


@dataclass(frozen=True)
class Guest:
    """The person a booking is under."""

    guest_id: str
    name: str


class BookingStatus(enum.Enum):
    """Where a booking stands."""

    CONFIRMED = "confirmed"
    CHECKED_IN = "checked_in"
    CHECKED_OUT = "checked_out"
    CANCELLED = "cancelled"
    NO_SHOW = "no_show"


@dataclass(frozen=True)
class Booking:
    """A stay in one room of a room type.

    The guest stays the nights from `check_in` up to but not including `check_out`.
    `children_ages` holds one age per child. `room` is the room number once one is assigned.
    `created_at` is timezone-aware.
    """

    booking_id: str
    guest_id: str
    room_type: str
    rate_plan: str
    check_in: date
    check_out: date
    adults: int
    children_ages: tuple[int, ...]
    status: BookingStatus
    created_at: datetime
    room: str | None = None


@dataclass(frozen=True)
class RatePlan:
    """A way of selling a room: refundable or not, with a discount off the seasonal rate."""

    code: str
    name: str
    refundable: bool
    discount_pct: Decimal = Decimal("0")
    min_nights: int = 1


@dataclass(frozen=True)
class Season:
    """The nightly rates of one room type from `start` to `end`, both included.

    `weekend_rate` applies to Friday and Saturday nights, `weekday_rate` to the rest.
    """

    room_type: str
    start: date
    end: date
    weekday_rate: Decimal
    weekend_rate: Decimal
