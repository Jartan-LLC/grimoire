"""The HTTP transport the client talks through."""

from dataclasses import dataclass
from typing import Protocol


class TransportError(Exception):
    """A request that got no usable answer."""


class Timeout(TransportError):
    """The service did not answer in time."""


@dataclass(frozen=True)
class Response:
    """A service's answer."""

    status: int
    body: dict[str, float]


class Transport(Protocol):
    """Sends GET requests; the deployment passes the real one, tests a fake."""

    def get(self, url: str) -> Response:
        """Fetch `url`."""
        ...
