"""python3 -m booklend overdue: list the loans past their due date."""

import os
import sys
from datetime import date
from pathlib import Path

from booklend import loans, members


def main(argv: list[str]) -> None:
    """Print each overdue loan with the member's name and the days late."""
    if argv != ["overdue"]:
        sys.exit("usage: python3 -m booklend overdue")
    data = Path(os.environ.get("BOOKLEND_DATA", "data"))
    people = members.load(data / "members.csv")
    for loan, days in loans.overdue(loans.load(data / "loans.csv"), date.today()):
        print(f"{days:>3} days  {loan.book}  ({people[loan.member_id]['name']})")


if __name__ == "__main__":
    main(sys.argv[1:])
