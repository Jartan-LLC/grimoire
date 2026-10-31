import dataclasses
import datetime

import pytest

from libcirc import CircError, ItemKind, Loan, Patron, PatronKind


def test_a_loan_starts_out_and_unrenewed_and_is_frozen():
    loan = Loan("B1", "p1", datetime.date(2026, 3, 2), datetime.date(2026, 3, 23))
    assert loan.returned is None and loan.renewals == 0
    with pytest.raises(dataclasses.FrozenInstanceError):
        loan.renewals = 1  # type: ignore[misc]


def test_kinds_and_error_type():
    assert ItemKind("dvd") is ItemKind.DVD
    assert Patron("p1", "Ann").kind is PatronKind.ADULT
    assert issubclass(CircError, ValueError)
