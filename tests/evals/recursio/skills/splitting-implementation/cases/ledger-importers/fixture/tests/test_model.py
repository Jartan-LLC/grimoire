from datetime import date
from decimal import Decimal

from ledger import Transaction


def test_transaction_holds_its_fields():
    t = Transaction(date(2026, 1, 5), Decimal("-12.50"), "Bakery")
    assert t.memo == ""
    assert t.amount < 0
