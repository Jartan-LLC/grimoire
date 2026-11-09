from decimal import Decimal

from exportkit.model import Record


def test_records_compare_by_value():
    assert Record(1, "a", Decimal("1.00")) == Record(1, "a", Decimal("1.00"))
