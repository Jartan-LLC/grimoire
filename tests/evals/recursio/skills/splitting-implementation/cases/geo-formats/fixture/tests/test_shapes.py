from geokit import Point, Polygon


def test_polygon_is_closed():
    ring = (Point(0, 0), Point(1, 0), Point(1, 1), Point(0, 0))
    assert Polygon(ring).ring[0] == Polygon(ring).ring[-1]
