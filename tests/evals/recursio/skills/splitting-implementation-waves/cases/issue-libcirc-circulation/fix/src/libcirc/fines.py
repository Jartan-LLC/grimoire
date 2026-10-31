"""Overdue fines and patron accounts."""

import datetime
from collections.abc import Collection, Iterable
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal

from .calendar import is_open
from .model import CircError, Item, ItemKind, Loan, Patron, PatronKind, Payment

RATES = {ItemKind.BOOK: Decimal("0.25"), ItemKind.DVD: Decimal("1.00")}
CAPS = {ItemKind.BOOK: Decimal("5.00"), ItemKind.DVD: Decimal("10.00")}
BLOCK_THRESHOLD = Decimal("10.00")
CENT = Decimal("0.01")


@dataclass(frozen=True)
class Account:
    """A patron's fines, payments and standing."""

    owed: Decimal
    paid: Decimal
    balance: Decimal
    blocked: bool


def overdue_days(loan: Loan, until: datetime.date, closures: Collection[datetime.date] = ()) -> int:
    """Open days after `loan.due`, through the return day or, while still out, through `until`."""
    last = loan.returned if loan.returned is not None else until
    day = loan.due + datetime.timedelta(days=1)
    count = 0
    while day <= last:
        count += is_open(day, closures)
        day += datetime.timedelta(days=1)
    return count


def fine(
    loan: Loan,
    item: Item,
    patron: Patron,
    until: datetime.date,
    closures: Collection[datetime.date] = (),
) -> Decimal:
    """The loan's fine: the first overdue open day is free, then the item's rate up to its cap.

    A child's card pays half of that, rounded.
    """
    if item.kind not in RATES:
        raise CircError(f"{item.kind.value} items are not fined: {item.barcode}")
    chargeable = max(overdue_days(loan, until, closures) - 1, 0)
    amount = min(RATES[item.kind] * chargeable, CAPS[item.kind])
    if patron.kind is PatronKind.CHILD:
        amount /= 2
    return amount.quantize(CENT, rounding=ROUND_HALF_UP)


def account(
    patron: Patron,
    loans: Iterable[Loan],
    items: Iterable[Item],
    payments: Iterable[Payment],
    today: datetime.date,
    closures: Collection[datetime.date] = (),
) -> Account:
    """The patron's fines on all their loans as of `today`, less their payments."""
    by_barcode = {item.barcode: item for item in items}
    owed = Decimal("0.00")
    for loan in loans:
        if loan.patron != patron.id:
            continue
        if loan.barcode not in by_barcode:
            raise CircError(f"loan for unknown item: {loan.barcode}")
        owed += fine(loan, by_barcode[loan.barcode], patron, today, closures)
    paid = sum((p.amount for p in payments if p.patron == patron.id), Decimal("0.00"))
    balance = owed - paid
    return Account(owed, paid, balance, balance >= BLOCK_THRESHOLD)
