from money import money


def test_positive() -> None:
    assert money(5) == '$5.00'
