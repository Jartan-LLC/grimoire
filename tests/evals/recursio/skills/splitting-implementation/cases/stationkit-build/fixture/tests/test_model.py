import dataclasses
from datetime import UTC, datetime

import pytest

from stationkit import Reading


def test_a_reading_leaves_unreported_fields_empty():
    r = Reading("north-field", datetime(2026, 7, 1, 12, 0, tzinfo=UTC), temperature_c=21.5)
    assert r.humidity_pct is None
    assert r.temperature_c == 21.5


def test_a_reading_cannot_be_changed():
    r = Reading("north-field", datetime(2026, 7, 1, 12, 0, tzinfo=UTC))
    with pytest.raises(dataclasses.FrozenInstanceError):
        r.temperature_c = 3.0  # type: ignore[misc]
