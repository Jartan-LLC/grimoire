"""When to sow."""

from datetime import date

from plantkit.model import load_garden
from plantkit.sowing import sow_dates


def test_sow_dates_by_date_then_name():
    assert sow_dates(load_garden("examples/garden.toml")) == [
        (date(2026, 2, 9), "onion"),
        (date(2026, 2, 23), "pepper"),
        (date(2026, 3, 9), "tomato"),
        (date(2026, 3, 23), "kale"),
        (date(2026, 3, 30), "carrot"),
        (date(2026, 4, 6), "bean"),
    ]
