from emails import is_valid_email


def test_plain() -> None:
    assert is_valid_email('ana@example.com')
