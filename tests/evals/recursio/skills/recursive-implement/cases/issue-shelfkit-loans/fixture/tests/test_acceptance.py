"""Acceptance tests for loans, fines, the overdue report and the command (#31)."""

import json
from datetime import date
from decimal import Decimal

import pytest

from shelfkit.cli import main
from shelfkit.fines import days_late, fine
from shelfkit.loans import checkout, return_book
from shelfkit.model import LoanError, load
from shelfkit.report import overdue_report

TODAY = date(2026, 10, 1)
LIBRARY = {
    "books": [
        {"isbn": "111", "title": "Dune", "price": "9.99"},
        {"isbn": "222", "title": "Emma", "price": "7.50"},
        {"isbn": "333", "title": "Ivanhoe", "price": "12.00"},
        {"isbn": "444", "title": "Kim", "price": "5.00"},
        {"isbn": "555", "title": "Nana", "price": "6.00"},
    ],
    "members": [{"id": "m1", "name": "Ana", "limit": 2}, {"id": "m2", "name": "Ben", "limit": 3}],
    "loans": [
        {"isbn": "222", "member": "m2", "out": "2026-09-01", "due": "2026-09-22", "back": None},
        {"isbn": "333", "member": "m2", "out": "2026-09-10", "due": "2026-09-29", "back": None},
        {"isbn": "444", "member": "m2", "out": "2026-08-01", "due": "2026-08-22", "back": "2026-08-25"},
    ],
}


@pytest.fixture
def path(tmp_path):
    target = tmp_path / "library.json"
    target.write_text(json.dumps(LIBRARY))
    return target


def test_checkout_moves_a_sunday_due_date_to_monday(path):
    library = load(path)
    loan = checkout(library, "111", "m1", date(2026, 10, 4))
    assert (loan.isbn, loan.member, loan.due, loan.back) == ("111", "m1", date(2026, 10, 26), None)
    assert loan in library.loans


def test_checkout_refuses_a_book_that_is_out(path):
    with pytest.raises(LoanError):
        checkout(load(path), "222", "m1", TODAY)


def test_checkout_refuses_a_member_at_the_limit(path):
    library = load(path)
    checkout(library, "111", "m1", TODAY)
    checkout(library, "444", "m1", TODAY)
    with pytest.raises(LoanError):
        checkout(library, "555", "m1", TODAY)


def test_return_closes_the_open_loan(path):
    library = load(path)
    assert return_book(library, "222", TODAY).back == TODAY
    assert [n for n in library.loans if n.isbn == "222" and n.back is None] == []
    with pytest.raises(LoanError):
        return_book(library, "222", TODAY)


def test_days_late_and_fines(path):
    emma, ivanhoe, kim = load(path).loans
    assert (days_late(emma, TODAY), fine(emma, TODAY)) == (9, Decimal("1.80"))
    assert (days_late(ivanhoe, TODAY), fine(ivanhoe, TODAY)) == (2, Decimal(0))
    assert (days_late(kim, TODAY), fine(kim, TODAY)) == (3, Decimal("0.60"))


def test_overdue_report(path):
    lines = overdue_report(load(path), TODAY)
    assert [(n.member, n.title, n.due, n.days_late, n.fine) for n in lines] == [
        ("Ben", "Emma", date(2026, 9, 22), 9, Decimal("1.80")),
        ("Ben", "Ivanhoe", date(2026, 9, 29), 2, Decimal(0)),
    ]


def test_cli_checkout_saves_the_loan(path, capsys):
    assert main(["checkout", str(path), "111", "m1", "--today", "2026-10-04"]) == 0
    assert capsys.readouterr().out == "due 2026-10-26\n"
    assert [n.member for n in load(path).loans if n.isbn == "111"] == ["m1"]


def test_cli_return_prints_the_fine(path, capsys):
    assert main(["return", str(path), "222", "--today", "2026-10-01"]) == 0
    assert capsys.readouterr().out == "fine 1.80\n"


def test_cli_overdue(path, capsys):
    assert main(["overdue", str(path), "--today", "2026-10-01"]) == 0
    assert capsys.readouterr().out == "Ben\tEmma\t2026-09-22\t9\t1.80\nBen\tIvanhoe\t2026-09-29\t2\t0.00\n"


def test_cli_loan_error_leaves_the_file(path, capsys):
    before = path.read_bytes()
    assert main(["checkout", str(path), "222", "m1", "--today", "2026-10-01"]) == 1
    assert capsys.readouterr().err.startswith("shelfkit: ")
    assert path.read_bytes() == before
