from wordstats import word_count


def test_counts() -> None:
    assert word_count("a b c") == 3
