import pytest

from clinicdesk.bookings import list_bookings
from clinicdesk.errors import BadRequest


def test_range_is_inclusive():
    rows = list_bookings({"from": "2026-10-05", "to": "2026-10-06"})
    assert [b["id"] for b in rows] == [1, 2]


def test_bad_date_is_rejected():
    with pytest.raises(BadRequest, match="YYYY-MM-DD"):
        list_bookings({"from": "5 Oct"})


def test_reversed_range_is_rejected():
    with pytest.raises(BadRequest, match="after"):
        list_bookings({"from": "2026-10-14", "to": "2026-10-01"})
