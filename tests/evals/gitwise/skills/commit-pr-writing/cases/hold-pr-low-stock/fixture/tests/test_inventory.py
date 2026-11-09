from inventory import total


def test_total() -> None:
    assert total({"a": 2, "b": 3}) == 5
