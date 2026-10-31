"""Pension contributions and student loan repayments, per year."""

from decimal import ROUND_HALF_UP, Decimal

PENNY = Decimal("0.01")

PENSION_RATE = Decimal("0.05")
PENSION_LOWER = Decimal("6240")
PENSION_UPPER = Decimal("50270")

LOAN_RATE = Decimal("0.09")
LOAN_THRESHOLD = Decimal("27295")


def pension(salary: Decimal) -> Decimal:
    """The employee's contribution: a share of the earnings between the two pension limits."""
    qualifying = min(salary, PENSION_UPPER) - PENSION_LOWER
    return max(qualifying * PENSION_RATE, Decimal(0)).quantize(PENNY, rounding=ROUND_HALF_UP)


def student_loan(salary: Decimal) -> Decimal:
    """The repayment: a share of the salary above the threshold."""
    above = salary - LOAN_THRESHOLD
    return max(above * LOAN_RATE, Decimal(0)).quantize(PENNY, rounding=ROUND_HALF_UP)
