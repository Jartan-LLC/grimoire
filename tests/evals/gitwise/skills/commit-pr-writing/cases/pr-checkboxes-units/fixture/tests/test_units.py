from units import km_to_miles


def test_km() -> None:
    assert round(km_to_miles(10), 2) == 6.21
