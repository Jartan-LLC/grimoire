"""Days late and fines."""

from datetime import date
from decimal import Decimal

from shelfkit.model import Loan

RATE = Decimal("0.20")
GRACE = 2


def days_late(loan: Loan, today: date) -> int:
    return max(0, ((loan.back or today) - loan.due).days)


def fine(loan: Loan, today: date) -> Decimal:
    late = days_late(loan, today)
    return RATE * late if late > GRACE else Decimal(0)
