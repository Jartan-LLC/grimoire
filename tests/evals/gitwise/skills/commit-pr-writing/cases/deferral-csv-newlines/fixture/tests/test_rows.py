from rows import split_row


def test_plain() -> None:
    assert split_row('a,b') == ['a', 'b']
