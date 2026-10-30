import dataclasses
from datetime import UTC, date, datetime
from decimal import ROUND_HALF_UP, Decimal

import pytest

from innkeeper import CENTS, Booking, BookingStatus, RatePlan


def _booking(**changes):
    base = Booking(
        booking_id="B1",
        guest_id="G1",
        room_type="DBL",
        rate_plan="FLEX",
        check_in=date(2026, 7, 3),
        check_out=date(2026, 7, 6),
        adults=2,
        children_ages=(5,),
        status=BookingStatus.CONFIRMED,
        created_at=datetime(2026, 5, 1, 9, 0, tzinfo=UTC),
    )
    return dataclasses.replace(base, **changes)


def test_a_new_booking_has_no_room_yet():
    booking = _booking()
    assert booking.room is None
    assert (booking.check_out - booking.check_in).days == 3


def test_bookings_cannot_be_changed_in_place():
    with pytest.raises(dataclasses.FrozenInstanceError):
        _booking().adults = 3  # type: ignore[misc]


def test_money_is_decimal():
    plan = RatePlan("FLEX", "Flexible", refundable=True)
    assert plan.discount_pct == Decimal("0")
    assert Decimal("10.005").quantize(CENTS, rounding=ROUND_HALF_UP) == Decimal("10.01")
