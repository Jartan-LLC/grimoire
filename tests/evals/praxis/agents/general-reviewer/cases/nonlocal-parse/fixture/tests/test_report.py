from decimal import Decimal

from tally.report import total


def test_total_sums_the_amount_column() -> None:
    assert total("sku,amount\na,1.50\nb,2.25\n") == Decimal("3.75")
