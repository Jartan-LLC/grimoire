# SPDX-License-Identifier: 0BSD
"""Tests for the check digits and the command."""

from isbntool.cli import main
from isbntool.isbn import is_valid


def test_isbn10_with_hyphens_and_x():
    assert is_valid("0-306-40615-2")
    assert is_valid("0-8044-2957-x")
    assert not is_valid("0-306-40615-3")


def test_isbn13():
    assert is_valid("978-0-306-40615-7")
    assert not is_valid("978-0-306-40615-8")


def test_check_prints_a_verdict_per_isbn(capsys):
    assert main(["check", "0-306-40615-2", "978-0-306-40615-8"]) == 1
    assert capsys.readouterr().out == "0-306-40615-2 valid\n978-0-306-40615-8 invalid\n"
