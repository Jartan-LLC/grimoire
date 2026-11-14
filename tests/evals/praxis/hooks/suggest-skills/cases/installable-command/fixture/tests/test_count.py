from wordcount.count import Counts, count


def test_counts():
    assert count("a b\nc\n") == Counts(2, 3, 6)
