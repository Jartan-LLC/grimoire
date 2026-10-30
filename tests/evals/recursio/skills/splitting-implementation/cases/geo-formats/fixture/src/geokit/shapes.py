"""Geometry types; coordinates are (longitude, latitude) in degrees."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Point:
    lon: float
    lat: float


@dataclass(frozen=True)
class LineString:
    points: tuple[Point, ...]


@dataclass(frozen=True)
class Polygon:
    """A closed ring: the first and last points are equal. No holes."""

    ring: tuple[Point, ...]
