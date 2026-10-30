"""The values the surveykit modules pass to one another."""

from dataclasses import dataclass
from datetime import datetime

# Mean Earth radius in metres (IUGG), for every spherical formula in the package.
MEAN_EARTH_RADIUS_M = 6371008.8


@dataclass(frozen=True)
class Ellipsoid:
    """A reference ellipsoid: semi-major axis `a` in metres and flattening `f`.

    `b` is the semi-minor axis, a * (1 - f).
    """

    name: str
    a: float
    f: float
    b: float


WGS84 = Ellipsoid(
    name="WGS84",
    a=6378137.0,
    f=1 / 298.257223563,
    b=6378137.0 * (1 - 1 / 298.257223563),
)


@dataclass(frozen=True)
class LatLon:
    """A position in decimal degrees: latitude north positive, longitude east positive.

    Latitude is within -90..90 and longitude within -180..180.
    """

    lat: float
    lon: float


@dataclass(frozen=True)
class TrackPoint:
    """One GPS fix: a timezone-aware time, a position, and the elevation in metres if known."""

    time: datetime
    position: LatLon
    elevation_m: float | None = None


@dataclass(frozen=True)
class Polygon:
    """A ring of vertices in either winding order; the first vertex is not repeated at the end."""

    vertices: tuple[LatLon, ...]


class GeodesyError(ValueError):
    """An input the package cannot work with, or a computation that did not converge."""
