from decimal import Decimal

from payroll.payslip import monthly_payslip


def test_monthly_payslip():
    slip = monthly_payslip(Decimal("30000"))
    assert (slip.gross, slip.tax, slip.pension, slip.student_loan) == (
        Decimal("2500.00"),
        Decimal("290.50"),
        Decimal("99.00"),
        Decimal("20.29"),
    )
    assert slip.net == Decimal("2090.21")


def test_bonus_taxed_at_the_marginal_rate():
    assert monthly_payslip(Decimal("30000"), Decimal("1000")).tax == Decimal("490.50")
