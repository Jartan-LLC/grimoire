from textstats import word_count


def test_spaces() -> None:
    assert word_count("a b c") == 3
