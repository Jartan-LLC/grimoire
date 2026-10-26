from dates import parse_date


def test_plain() -> None:
    assert parse_date('2026-01-05').day == 5
