import dataclasses
from datetime import UTC, datetime

import pytest

from surveykit import WGS84, LatLon, Polygon, TrackPoint


def test_wgs84_has_its_defining_constants():
    assert WGS84.a == 6378137.0
    assert 1 / WGS84.f == pytest.approx(298.257223563)
    assert WGS84.b == pytest.approx(6356752.314245, abs=1e-6)


def test_a_track_point_may_lack_an_elevation():
    p = TrackPoint(datetime(2026, 5, 4, 9, 30, tzinfo=UTC), LatLon(52.2053, 0.1218))
    assert p.elevation_m is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        p.elevation_m = 12.0  # type: ignore[misc]


def test_a_polygon_holds_its_ring_unclosed():
    ring = Polygon((LatLon(0, 0), LatLon(0, 1), LatLon(1, 1)))
    assert len(ring.vertices) == 3
