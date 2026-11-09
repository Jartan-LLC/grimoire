from textstats import word_count


def test_counts_words() -> None:
    assert word_count("a b c") == 3
