# SPDX-License-Identifier: 0BSD
"""Tests for check --to13."""

from isbntool.cli import main


def test_isbn10_becomes_isbn13(capsys):
    assert main(["check", "--to13", "0-306-40615-2", "0-8044-2957-X"]) == 0
    assert capsys.readouterr().out == "9780306406157\n9780804429573\n"


def test_isbn13_prints_as_digits(capsys):
    assert main(["check", "--to13", "978 0 306 40615 7"]) == 0
    assert capsys.readouterr().out == "9780306406157\n"


def test_invalid_keeps_its_line_and_exit_status(capsys):
    assert main(["check", "--to13", "0-306-40615-3", "0-306-40615-2"]) == 1
    assert capsys.readouterr().out == "0-306-40615-3 invalid\n9780306406157\n"


def test_without_the_option_nothing_changes(capsys):
    assert main(["check", "0-306-40615-2"]) == 0
    assert capsys.readouterr().out == "0-306-40615-2 valid\n"
