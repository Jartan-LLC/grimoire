from inventory import get_qty


def test_unknown_is_zero() -> None:
    assert get_qty({}, "x") == 0
