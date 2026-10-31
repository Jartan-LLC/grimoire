from decimal import Decimal

from payroll.brackets import bracket_for, income_tax


def test_income_tax_by_slices():
    assert income_tax(Decimal("10000")) == Decimal("0.00")
    assert income_tax(Decimal("30000")) == Decimal("3486.00")
    assert income_tax(Decimal("60000")) == Decimal("11432.00")


def test_income_inside_a_bracket():
    assert bracket_for(Decimal("30000")).rate == Decimal("0.20")
    assert bracket_for(Decimal("200000")).rate == Decimal("0.45")


def test_income_on_a_bound_stays_in_the_lower_bracket():
    assert bracket_for(Decimal("50270")).rate == Decimal("0.20")
    assert bracket_for(Decimal("50270.01")).rate == Decimal("0.40")
