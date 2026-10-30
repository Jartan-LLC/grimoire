"""The records the transitkit modules pass to one another."""

import enum
from dataclasses import dataclass, field
from datetime import date

# Seconds in a service day. A StopTime of a trip that runs past midnight is larger than this.
SECONDS_PER_DAY = 86400

# Mean Earth radius in metres, for every great-circle distance in the package.
EARTH_RADIUS_M = 6371008.8


class RouteType(enum.Enum):
    """The kind of vehicle on a route, with the GTFS route_type codes."""

    TRAM = 0
    SUBWAY = 1
    RAIL = 2
    BUS = 3
    FERRY = 4


@dataclass(frozen=True)
class Stop:
    """A place where vehicles stop; lat and lon are WGS84 degrees."""

    stop_id: str
    name: str
    lat: float
    lon: float


@dataclass(frozen=True)
class Route:
    """A line as the public knows it; one of short_name and long_name may be empty."""

    route_id: str
    short_name: str
    long_name: str
    route_type: RouteType


@dataclass(frozen=True)
class Trip:
    """One run of a vehicle along a route on the days its service runs."""

    trip_id: str
    route_id: str
    service_id: str
    headsign: str = ""
    direction_id: int | None = None


@dataclass(frozen=True)
class StopTime:
    """A trip's call at a stop.

    `arrival` and `departure` are seconds after midnight of the service day the trip runs on,
    so a trip that leaves at 23:50 and arrives at 00:20 the next morning has an arrival of
    87600, written 24:20:00 in the feed. Calls of a trip are ordered by `stop_sequence`, which
    increases along the trip but need not be consecutive.
    """

    trip_id: str
    stop_id: str
    stop_sequence: int
    arrival: int
    departure: int


@dataclass(frozen=True)
class Service:
    """The regular days a set of trips runs.

    `weekdays` holds seven flags, Monday first. `start` and `end` are both included.
    """

    service_id: str
    weekdays: tuple[bool, bool, bool, bool, bool, bool, bool]
    start: date
    end: date


class ExceptionKind(enum.Enum):
    """Whether a ServiceException adds or removes a day, with the GTFS exception_type codes."""

    ADDED = 1
    REMOVED = 2


@dataclass(frozen=True)
class ServiceException:
    """One date on which a service runs although its weekdays say not, or the reverse."""

    service_id: str
    on: date
    kind: ExceptionKind


@dataclass
class Feed:
    """A whole timetable. A service id may appear only in `exceptions`."""

    stops: list[Stop] = field(default_factory=list)
    routes: list[Route] = field(default_factory=list)
    trips: list[Trip] = field(default_factory=list)
    stop_times: list[StopTime] = field(default_factory=list)
    services: list[Service] = field(default_factory=list)
    exceptions: list[ServiceException] = field(default_factory=list)
