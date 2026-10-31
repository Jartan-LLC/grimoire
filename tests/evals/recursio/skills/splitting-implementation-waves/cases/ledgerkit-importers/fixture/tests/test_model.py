from datetime import date
from decimal import Decimal

from ledgerkit import ImportResult, Transaction


def test_transaction_defaults():
    t = Transaction(date(2026, 3, 1), Decimal("-3.50"), "Cafe Uno")
    assert t.currency == "EUR"
    assert t.category is None


def test_import_result_starts_empty():
    r = ImportResult()
    assert r.transactions == [] and r.skipped == []
