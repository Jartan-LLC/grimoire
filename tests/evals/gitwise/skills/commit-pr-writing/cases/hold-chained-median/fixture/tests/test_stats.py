from stats import mean


def test_mean() -> None:
    assert mean([1, 2, 3]) == 2
