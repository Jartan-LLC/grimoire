"""Planted acceptance tests for reports."""

from datetime import date
from decimal import Decimal

import pytest

from ledgerkit import Transaction
from ledgerkit.reports import MonthTotals, by_category, monthly_totals

TXS = [
    Transaction(date(2026, 1, 5), Decimal("-10.00"), "Cafe Uno", category="eating out"),
    Transaction(date(2026, 1, 9), Decimal("2000.00"), "ACME", category="salary"),
    Transaction(date(2026, 3, 2), Decimal("-40.00"), "Green Market", category="groceries"),
    Transaction(date(2026, 3, 3), Decimal("-500.00"), "Me", category="transfer:Savings"),
    Transaction(date(2026, 3, 4), Decimal("-5.00"), "Kiosk"),
]


def test_monthly_totals_fills_gaps():
    m = monthly_totals(TXS)
    assert list(m) == ["2026-01", "2026-02", "2026-03"]
    assert m["2026-01"] == MonthTotals(Decimal("2000.00"), Decimal("10.00"), Decimal("1990.00"))
    assert m["2026-02"] == MonthTotals(Decimal("0"), Decimal("0"), Decimal("0"))


def test_by_category_leaves_out_transfers_and_income():
    assert by_category(TXS, "2026-03") == [("groceries", Decimal("40.00")), ("uncategorized", Decimal("5.00"))]


def test_mixed_currencies_rejected():
    with pytest.raises(ValueError):
        monthly_totals([*TXS, Transaction(date(2026, 3, 5), Decimal("-1"), "X", currency="USD")])
