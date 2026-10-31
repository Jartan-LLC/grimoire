"""The holds queue: placing holds and handing returned items to the next patron."""

import datetime
from collections.abc import Collection
from dataclasses import dataclass

from .calendar import add_open_days
from .model import CircError, Hold, Loan

MAX_HOLDS = 10
PICKUP_OPEN_DAYS = 7


@dataclass(frozen=True)
class Pickup:
    """An item set aside for `patron` until the end of the day `expires`."""

    patron: str
    barcode: str
    expires: datetime.date


def place(
    holds: list[Hold], barcode: str, patron: str, when: datetime.datetime, loans: list[Loan]
) -> list[Hold]:
    """A new list with the patron's hold on `barcode` added at the end."""
    if any(h.barcode == barcode and h.patron == patron for h in holds):
        raise CircError(f"{patron} already holds {barcode}")
    if any(ln.barcode == barcode and ln.patron == patron and ln.returned is None for ln in loans):
        raise CircError(f"{patron} already has {barcode} on loan")
    if sum(h.patron == patron for h in holds) >= MAX_HOLDS:
        raise CircError(f"{patron} already has {MAX_HOLDS} holds")
    return [*holds, Hold(barcode, patron, when)]


def queue(holds: list[Hold], barcode: str) -> list[Hold]:
    """The holds on `barcode`, earliest placed first."""
    return sorted((h for h in holds if h.barcode == barcode), key=lambda h: h.placed)


def on_return(
    holds: list[Hold],
    barcode: str,
    today: datetime.date,
    closures: Collection[datetime.date] = (),
) -> tuple[Pickup | None, list[Hold]]:
    """Hand `barcode` to the first hold in its queue, removing that hold from the list."""
    waiting = queue(holds, barcode)
    if not waiting:
        return None, list(holds)
    first = waiting[0]
    remaining = [h for h in holds if h is not first]
    expires = add_open_days(today, PICKUP_OPEN_DAYS, closures)
    return Pickup(first.patron, barcode, expires), remaining


def expire(
    pickup: Pickup,
    holds: list[Hold],
    today: datetime.date,
    closures: Collection[datetime.date] = (),
) -> tuple[Pickup | None, list[Hold]]:
    """The pickup unchanged until `today` is past its expiry, then the next hold's pickup."""
    if today <= pickup.expires:
        return pickup, holds
    return on_return(holds, pickup.barcode, today, closures)
