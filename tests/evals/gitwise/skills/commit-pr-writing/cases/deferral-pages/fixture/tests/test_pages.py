from pages import page_count


def test_partial() -> None:
    assert page_count(11, 5) == 3
