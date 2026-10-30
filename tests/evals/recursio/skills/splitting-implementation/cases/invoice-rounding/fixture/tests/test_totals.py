from decimal import Decimal

from invoicer.totals import invoice_total, line_total


def test_line_total_rounds_half_up():
    assert line_total(3, Decimal("0.335")) == Decimal("1.01")


def test_vat_is_added():
    assert invoice_total([(1, Decimal("10.00"))], Decimal("0.2")) == Decimal("12.00")


def test_total_matches_the_printed_lines():
    lines = [(3, Decimal("0.335")), (1, Decimal("0.335"))]
    assert invoice_total(lines, Decimal("0")) == Decimal("1.35")
