from datetime import date

from booklend.loans import Loan, overdue


def test_overdue_skips_returned_and_not_yet_due():
    loans = [
        Loan("Emma", "m1", date(2026, 10, 1), returned=False),
        Loan("Dracula", "m2", date(2026, 10, 1), returned=True),
        Loan("Ulysses", "m3", date(2026, 10, 30), returned=False),
    ]
    assert overdue(loans, date(2026, 10, 8)) == [(loans[0], 7)]
