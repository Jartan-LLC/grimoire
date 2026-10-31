"""One month's payslip."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from payroll.brackets import income_tax, marginal_rate
from payroll.deductions import pension, student_loan

PENNY = Decimal("0.01")


@dataclass(frozen=True)
class Payslip:
    gross: Decimal
    tax: Decimal
    pension: Decimal
    student_loan: Decimal
    net: Decimal


def _month(annual: Decimal) -> Decimal:
    return (annual / 12).quantize(PENNY, rounding=ROUND_HALF_UP)


def monthly_payslip(salary: Decimal, bonus: Decimal = Decimal(0)) -> Payslip:
    """The payslip for one month of `salary`, plus a one-off `bonus` taxed at the marginal rate."""
    bonus_tax = (bonus * marginal_rate(salary)).quantize(PENNY, rounding=ROUND_HALF_UP)
    gross = _month(salary) + bonus
    tax = _month(income_tax(salary)) + bonus_tax
    contribution = _month(pension(salary))
    loan = _month(student_loan(salary))
    return Payslip(gross, tax, contribution, loan, gross - tax - contribution - loan)
