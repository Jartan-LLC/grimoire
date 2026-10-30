from decimal import Decimal

from payroll.deductions import pension, student_loan


def test_pension_on_qualifying_earnings():
    assert pension(Decimal("30000")) == Decimal("1188.00")
    assert pension(Decimal("5000")) == Decimal("0.00")


def test_student_loan_above_the_threshold():
    assert student_loan(Decimal("30000")) == Decimal("243.45")
    assert student_loan(Decimal("20000")) == Decimal("0.00")
