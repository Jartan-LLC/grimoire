from dates import days_in_year


def test_days() -> None:
    assert days_in_year(True) == 366
