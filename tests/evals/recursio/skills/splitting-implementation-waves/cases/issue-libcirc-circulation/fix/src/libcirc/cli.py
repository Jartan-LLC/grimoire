"""The `libcirc` command: overdue loans, patron accounts and hold queues from CSV files."""

import argparse
import csv
import datetime
import decimal
import sys
from collections.abc import Callable, Sequence
from pathlib import Path
from typing import TypeVar

from . import fines, holds, loans
from .model import CircError, Hold, Item, ItemKind, Loan, Patron, PatronKind, Payment

T = TypeVar("T")

BAD_INPUT = 2


def _read(path: str, build: Callable[[dict[str, str]], T]) -> list[T]:
    """One record per CSV row, any unreadable file or malformed row reported as a CircError."""
    try:
        with open(path, newline="") as f:
            return [build(row) for row in csv.DictReader(f)]
    except OSError as e:
        raise CircError(f"cannot read {path}: {e.strerror}") from e
    except (KeyError, ValueError, TypeError, decimal.InvalidOperation) as e:
        raise CircError(f"bad row in {path}: {e!r}") from e


def _items(path: str) -> list[Item]:
    return _read(path, lambda r: Item(r["barcode"], r["title"], ItemKind(r["kind"])))


def _patrons(path: str) -> list[Patron]:
    return _read(path, lambda r: Patron(r["id"], r["name"], PatronKind(r["kind"])))


def _loans(path: str) -> list[Loan]:
    return _read(
        path,
        lambda r: Loan(
            r["barcode"],
            r["patron"],
            datetime.date.fromisoformat(r["out"]),
            datetime.date.fromisoformat(r["due"]),
            datetime.date.fromisoformat(r["returned"]) if r["returned"] else None,
            int(r["renewals"]),
        ),
    )


def _holds(path: str) -> list[Hold]:
    return _read(
        path,
        lambda r: Hold(r["barcode"], r["patron"], datetime.datetime.fromisoformat(r["placed"])),
    )


def _payments(path: str) -> list[Payment]:
    return _read(
        path,
        lambda r: Payment(r["patron"], datetime.date.fromisoformat(r["day"]), decimal.Decimal(r["amount"])),
    )


def _closures(path: str | None) -> set[datetime.date]:
    if path is None:
        return set()
    try:
        lines = Path(path).read_text().splitlines()
        return {datetime.date.fromisoformat(line.strip()) for line in lines if line.strip()}
    except OSError as e:
        raise CircError(f"cannot read {path}: {e.strerror}") from e
    except ValueError as e:
        raise CircError(f"bad closure day in {path}: {e}") from e


def _date(text: str) -> datetime.date:
    try:
        return datetime.date.fromisoformat(text)
    except ValueError as e:
        raise argparse.ArgumentTypeError(f"not an ISO date: {text}") from e


def _overdue(args: argparse.Namespace) -> int:
    known = {item.barcode for item in _items(args.items)}
    closures = _closures(args.closures)
    for loan in loans.overdue(_loans(args.loans), args.today):
        if loan.barcode not in known:
            raise CircError(f"loan for unknown item: {loan.barcode}")
        days = fines.overdue_days(loan, args.today, closures)
        print(loan.barcode, loan.patron, loan.due.isoformat(), days)
    return 0


def _account(args: argparse.Namespace) -> int:
    patron = next((p for p in _patrons(args.patrons) if p.id == args.patron), None)
    if patron is None:
        raise CircError(f"unknown patron: {args.patron}")
    acct = fines.account(
        patron,
        _loans(args.loans),
        _items(args.items),
        _payments(args.payments),
        args.today,
        _closures(args.closures),
    )
    print("owed", acct.owed)
    print("paid", acct.paid)
    print("balance", acct.balance)
    print("blocked" if acct.blocked else "ok")
    return 1 if acct.blocked else 0


def _queue(args: argparse.Namespace) -> int:
    for hold in holds.queue(_holds(args.holds), args.barcode):
        print(hold.patron)
    return 0


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="libcirc", description="Library circulation.")
    sub = parser.add_subparsers(dest="command", required=True)

    overdue = sub.add_parser("overdue", help="list overdue loans")
    overdue.add_argument("items")
    overdue.add_argument("loans")
    overdue.add_argument("--today", type=_date, required=True)
    overdue.add_argument("--closures")
    overdue.set_defaults(run=_overdue)

    account = sub.add_parser("account", help="show a patron's fines and standing")
    for name in ("items", "patrons", "loans", "payments"):
        account.add_argument(name)
    account.add_argument("--patron", required=True)
    account.add_argument("--today", type=_date, required=True)
    account.add_argument("--closures")
    account.set_defaults(run=_account)

    queue = sub.add_parser("queue", help="list the patrons holding a barcode")
    queue.add_argument("holds")
    queue.add_argument("--barcode", required=True)
    queue.set_defaults(run=_queue)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the command and return its exit status."""
    args = _parser().parse_args(argv)
    try:
        return args.run(args)
    except CircError as e:
        print(e, file=sys.stderr)
        return BAD_INPUT
