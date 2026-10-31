"""Planted acceptance tests: one basic check per module and two for the command."""

import contextlib
import datetime as dt
import io
import pathlib
import sys
import tempfile
import unittest
from decimal import Decimal as D

# conftest.py puts src/ on the path for pytest; unittest does not read it.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from libcirc import CircError, Hold, Item, ItemKind, Loan, Patron, PatronKind, Payment
from libcirc import cli, fines, holds, loans

BOOK = Item("B1", "Dune", ItemKind.BOOK)
DVD = Item("D1", "Alien", ItemKind.DVD)
ANN = Patron("ann", "Ann")
KIT = Patron("kit", "Kit", PatronKind.CHILD)

BOOK_LOAN = Loan("B1", "ann", dt.date(2026, 2, 9), dt.date(2026, 3, 2), returned=dt.date(2026, 3, 9))
DVD_LOAN = Loan("D1", "ann", dt.date(2026, 2, 23), dt.date(2026, 3, 2))

HOLDS = [
    Hold("B1", "bob", dt.datetime(2026, 3, 1, 10)),
    Hold("B1", "ann", dt.datetime(2026, 3, 1, 9)),
]


def run(argv):
    """The exit code of `cli.main(argv)` and what it printed."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(argv)
    return code, out.getvalue()


class PlantedTest(unittest.TestCase):
    def test_due_dates_and_renewal_refused_by_a_hold(self):
        assert loans.due_date(BOOK, dt.date(2026, 3, 7)) == dt.date(2026, 3, 28)
        assert loans.due_date(BOOK, dt.date(2026, 3, 7), {dt.date(2026, 3, 28)}) == dt.date(2026, 3, 30)
        loan = loans.checkout(DVD, ANN, dt.date(2026, 3, 2), [])
        assert (loan.barcode, loan.patron, loan.due) == ("D1", "ann", dt.date(2026, 3, 9))
        renewed = loans.renew(loan, DVD, dt.date(2026, 3, 9), [])
        assert (renewed.due, renewed.renewals) == (dt.date(2026, 3, 16), 1)
        with self.assertRaises(CircError):
            loans.renew(loan, DVD, dt.date(2026, 3, 9), [Hold("D1", "bob", dt.datetime(2026, 3, 3, 9))])

    def test_fines_grace_cap_child_and_account(self):
        assert fines.overdue_days(BOOK_LOAN, dt.date(2026, 3, 30)) == 6
        assert fines.fine(BOOK_LOAN, BOOK, ANN, dt.date(2026, 3, 30)) == D("1.25")
        assert fines.fine(BOOK_LOAN, BOOK, KIT, dt.date(2026, 3, 30)) == D("0.63")
        assert fines.fine(BOOK_LOAN, BOOK, ANN, dt.date(2026, 3, 30), {dt.date(2026, 3, 4)}) == D("1.00")
        assert fines.fine(DVD_LOAN, DVD, ANN, dt.date(2026, 3, 30)) == D("10.00")
        acct = fines.account(
            ANN, [BOOK_LOAN, DVD_LOAN], [BOOK, DVD], [Payment("ann", dt.date(2026, 3, 9), D("1.00"))],
            dt.date(2026, 3, 30),
        )
        assert (acct.owed, acct.paid, acct.balance, acct.blocked) == (D("11.25"), D("1.00"), D("10.25"), True)

    def test_holds_queue_pickup_and_expiry(self):
        assert [h.patron for h in holds.queue(HOLDS, "B1")] == ["ann", "bob"]
        with self.assertRaises(CircError):
            holds.place(HOLDS, "B1", "ann", dt.datetime(2026, 3, 2, 9), [])
        pickup, rest = holds.on_return(HOLDS, "B1", dt.date(2026, 3, 7))
        assert (pickup.patron, pickup.expires) == ("ann", dt.date(2026, 3, 16))
        assert [h.patron for h in rest] == ["bob"]
        same, _ = holds.expire(pickup, rest, dt.date(2026, 3, 16))
        assert same == pickup
        nxt, left = holds.expire(pickup, rest, dt.date(2026, 3, 17))
        assert (nxt.patron, nxt.expires, list(left)) == ("bob", dt.date(2026, 3, 25), [])

    def test_cli_queue_and_account(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            h = tmp_path / "holds.csv"
            h.write_text("barcode,patron,placed\nB1,bob,2026-03-01T10:00\nB1,ann,2026-03-01T09:00\n")
            code, out = run(["queue", str(h), "--barcode", "B1"])
            assert code == 0
            assert out.splitlines() == ["ann", "bob"]
            (tmp_path / "items.csv").write_text("barcode,title,kind\nB1,Dune,book\nD1,Alien,dvd\n")
            (tmp_path / "patrons.csv").write_text("id,name,kind\nann,Ann,adult\n")
            (tmp_path / "loans.csv").write_text(
                "barcode,patron,out,due,returned,renewals\n"
                "B1,ann,2026-02-09,2026-03-02,2026-03-09,0\n"
                "D1,ann,2026-02-23,2026-03-02,,0\n"
            )
            (tmp_path / "payments.csv").write_text("patron,day,amount\nann,2026-03-09,1.00\n")
            files = [str(tmp_path / n) for n in ("items.csv", "patrons.csv", "loans.csv", "payments.csv")]
            code, out = run(["account", *files, "--patron", "ann", "--today", "2026-03-30"])
            assert code == 1
            out = out.splitlines()
            assert "balance 10.25" in out and out[-1] == "blocked"
