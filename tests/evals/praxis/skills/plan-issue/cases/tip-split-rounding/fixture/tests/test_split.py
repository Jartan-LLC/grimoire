from tabsplit.split import split


def test_even_split():
    assert split(1200, 3) == [400, 400, 400]


def test_one_person_pays_everything():
    assert split(999, 1) == [999]
