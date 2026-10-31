"""The data model's JSON file."""

from datetime import date
from decimal import Decimal

from shelfkit.model import Book, Library, Loan, Member, load, save


def test_save_then_load_round_trips(tmp_path):
    library = Library(
        {"1": Book("1", "Dune", Decimal("9.99"))},
        {"m1": Member("m1", "Ana", 2)},
        [Loan("1", "m1", date(2026, 9, 1), date(2026, 9, 22), date(2026, 9, 20))],
    )
    save(library, tmp_path / "library.json")
    assert load(tmp_path / "library.json") == library
