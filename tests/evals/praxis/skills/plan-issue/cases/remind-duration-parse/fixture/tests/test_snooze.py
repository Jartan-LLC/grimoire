from datetime import timedelta

import pytest

from remindme.snooze import _parse_duration


def test_parses_mixed_units():
    assert _parse_duration("1h30m") == timedelta(minutes=90)
    assert _parse_duration("2d") == timedelta(days=2)


def test_rejects_other_text():
    with pytest.raises(ValueError):
        _parse_duration("90")
