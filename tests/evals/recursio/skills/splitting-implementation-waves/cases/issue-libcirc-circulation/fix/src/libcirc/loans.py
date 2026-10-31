"""Lending items and renewing loans."""

import dataclasses
import datetime
from collections.abc import Collection, Iterable

from .calendar import next_open
from .model import CircError, Hold, Item, ItemKind, Loan, Patron, PatronKind

LOAN_DAYS = {ItemKind.BOOK: 21, ItemKind.DVD: 7}
LOAN_LIMITS = {PatronKind.CHILD: 5, PatronKind.ADULT: 15}
MAX_RENEWALS = 2
MAX_OVERDUE_DAYS_TO_RENEW = 14


def due_date(
    item: Item, out: datetime.date, closures: Collection[datetime.date] = ()
) -> datetime.date:
    """The day `item` is due when lent on `out`, moved to the next open day."""
    if item.kind not in LOAN_DAYS:
        raise CircError(f"{item.barcode} is a {item.kind.value} item and cannot be lent")
    return next_open(out + datetime.timedelta(days=LOAN_DAYS[item.kind]), closures)


def checkout(
    item: Item,
    patron: Patron,
    today: datetime.date,
    loans: Iterable[Loan],
    closures: Collection[datetime.date] = (),
) -> Loan:
    """Lend `item` to `patron`, refusing if it is out, the patron is overdue or at their limit."""
    unreturned = [loan for loan in loans if loan.returned is None]
    if any(loan.barcode == item.barcode for loan in unreturned):
        raise CircError(f"{item.barcode} is already out on loan")
    mine = [loan for loan in unreturned if loan.patron == patron.id]
    if any(loan.due < today for loan in mine):
        raise CircError(f"{patron.id} has an overdue loan")
    limit = LOAN_LIMITS[patron.kind]
    if len(mine) >= limit:
        raise CircError(f"{patron.id} already has {limit} loans, the limit for a {patron.kind.value} card")
    return Loan(item.barcode, patron.id, today, due_date(item, today, closures))


def renew(
    loan: Loan,
    item: Item,
    today: datetime.date,
    holds: Iterable[Hold],
    closures: Collection[datetime.date] = (),
) -> Loan:
    """The loan with a new due date and one more renewal, refused when it may not be renewed."""
    if loan.returned is not None:
        raise CircError(f"{loan.barcode} has been returned and cannot be renewed")
    if loan.renewals >= MAX_RENEWALS:
        raise CircError(f"{loan.barcode} has already been renewed {MAX_RENEWALS} times")
    if any(hold.barcode == loan.barcode for hold in holds):
        raise CircError(f"{loan.barcode} is held by another patron")
    if (today - loan.due).days > MAX_OVERDUE_DAYS_TO_RENEW:
        raise CircError(f"{loan.barcode} is more than {MAX_OVERDUE_DAYS_TO_RENEW} days overdue")
    return dataclasses.replace(
        loan, due=due_date(item, today, closures), renewals=loan.renewals + 1
    )


def overdue(loans: Iterable[Loan], today: datetime.date) -> list[Loan]:
    """The unreturned loans due before `today`, by due date and then barcode."""
    late = [loan for loan in loans if loan.returned is None and loan.due < today]
    return sorted(late, key=lambda loan: (loan.due, loan.barcode))
