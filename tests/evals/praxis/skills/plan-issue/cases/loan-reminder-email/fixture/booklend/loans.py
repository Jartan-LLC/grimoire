"""Loans, kept in loans.csv: book, member_id, due (YYYY-MM-DD), returned (empty until returned)."""

import csv
from dataclasses import dataclass
from datetime import date
from pathlib import Path


@dataclass
class Loan:
    """One book lent to one member."""

    book: str
    member_id: str
    due: date
    returned: bool


def load(path: Path) -> list[Loan]:
    """Every loan in the file."""
    with path.open(newline="") as handle:
        return [
            Loan(row["book"], row["member_id"], date.fromisoformat(row["due"]), bool(row["returned"]))
            for row in csv.DictReader(handle)
        ]


def overdue(loans: list[Loan], today: date) -> list[tuple[Loan, int]]:
    """Each loan not yet returned and past its due date, with how many days late it is."""
    return [(loan, (today - loan.due).days) for loan in loans if not loan.returned and loan.due < today]
