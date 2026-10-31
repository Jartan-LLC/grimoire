import dataclasses

import pytest

from zonekit import MX, Record, RType, Zone


def test_record_types_carry_their_wire_codes():
    assert RType.MX.value == 15
    assert RType.CAA.value == 257


def test_a_record_cannot_be_changed():
    r = Record("example.com.", 3600, "IN", RType.MX, MX(10, "mail.example.com."))
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.ttl = 60  # type: ignore[misc]


def test_a_zone_keeps_its_records_in_order():
    first = Record("example.com.", 3600, "IN", RType.MX, MX(10, "a.example.com."))
    second = Record("example.com.", 3600, "IN", RType.MX, MX(20, "b.example.com."))
    assert Zone("example.com.", (first, second)).records == (first, second)
