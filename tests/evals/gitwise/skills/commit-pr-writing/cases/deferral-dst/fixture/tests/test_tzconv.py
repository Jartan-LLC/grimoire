from tzconv import to_utc


def test_parses() -> None:
    assert to_utc("2026-01-01 00:00", "UTC").hour == 0
