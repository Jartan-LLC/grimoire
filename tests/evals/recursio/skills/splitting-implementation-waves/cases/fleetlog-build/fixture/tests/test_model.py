import dataclasses
import datetime
from decimal import Decimal

import pytest

from fleetlog import FillUp, FleetError, FuelKind


def test_a_fill_up_is_full_by_default_and_frozen():
    f = FillUp("AB12", datetime.date(2026, 3, 1), 10000, Decimal("40"), Decimal("70.00"))
    assert f.full is True
    with pytest.raises(dataclasses.FrozenInstanceError):
        f.litres = Decimal("1")  # type: ignore[misc]


def test_fuel_kinds_and_error_type():
    assert FuelKind("electric") is FuelKind.ELECTRIC
    assert issubclass(FleetError, ValueError)
