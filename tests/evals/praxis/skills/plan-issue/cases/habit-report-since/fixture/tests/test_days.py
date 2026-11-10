import pytest

from habits.days import format_day, parse_day


def test_round_trip():
    assert format_day(parse_day("2026-10-03")) == "2026-10-03"


def test_bad_day():
    with pytest.raises(ValueError):
        parse_day("Oct 3")
