from blogtools.text import reading_time, word_count


def test_word_count():
    assert word_count("a b  c") == 3


def test_reading_time():
    assert reading_time("word " * 500) == 3
