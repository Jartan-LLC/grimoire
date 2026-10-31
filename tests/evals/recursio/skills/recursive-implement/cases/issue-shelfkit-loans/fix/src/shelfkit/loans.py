"""Checkouts and returns."""

from dataclasses import replace
from datetime import date, timedelta

from shelfkit.model import Library, Loan, LoanError

SUNDAY = 6


def checkout(library: Library, isbn: str, member: str, today: date, days: int = 21) -> Loan:
    if isbn not in library.books:
        raise LoanError(f"no book {isbn}")
    if member not in library.members:
        raise LoanError(f"no member {member}")
    if any(n.isbn == isbn and n.back is None for n in library.loans):
        raise LoanError(f"book {isbn} is out")
    if sum(n.member == member and n.back is None for n in library.loans) >= library.members[member].limit:
        raise LoanError(f"member {member} is at the limit")
    due = today + timedelta(days=days)
    if due.weekday() == SUNDAY:
        due += timedelta(days=1)
    loan = Loan(isbn, member, today, due)
    library.loans.append(loan)
    return loan


def return_book(library: Library, isbn: str, today: date) -> Loan:
    for index, loan in enumerate(library.loans):
        if loan.isbn == isbn and loan.back is None:
            library.loans[index] = replace(loan, back=today)
            return library.loans[index]
    raise LoanError(f"book {isbn} is not out")
