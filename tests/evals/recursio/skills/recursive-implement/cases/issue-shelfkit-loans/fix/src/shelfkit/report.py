"""The overdue report."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from shelfkit.fines import days_late, fine
from shelfkit.model import Library


@dataclass(frozen=True)
class OverdueLine:
    member: str
    title: str
    due: date
    days_late: int
    fine: Decimal


def overdue_report(library: Library, today: date) -> list[OverdueLine]:
    lines = [
        OverdueLine(
            library.members[n.member].name, library.books[n.isbn].title, n.due, days_late(n, today), fine(n, today)
        )
        for n in library.loans
        if n.back is None and n.due < today
    ]
    return sorted(lines, key=lambda line: (-line.days_late, line.title))
