from geokit.model import Point


def test_elevation_is_optional():
    assert Point(1.0, 2.0).ele is None
