from datetime import date

from pantry.utils import days_left, format_quantity, item_title, parse_best_before, to_grams


def test_units():
    assert to_grams(2, "kg") == 2000


def test_dates():
    assert parse_best_before("05/03/2026") == date(2026, 3, 5)
    assert days_left(date(2026, 3, 5), date(2026, 3, 1)) == 4


def test_text():
    assert item_title("salt and pepper") == "Salt and Pepper"
    assert format_quantity(2, "box") == "2 boxes"
