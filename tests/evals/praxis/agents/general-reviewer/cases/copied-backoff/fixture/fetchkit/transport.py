"""The one place a request leaves the process; tests replace `send`."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Response:
    """What a request came back with."""

    status: int
    body: str

    @property
    def ok(self) -> bool:
        """Whether the status is a success."""
        return 200 <= self.status < 300


def send(url: str) -> Response:
    """Send a GET to `url`."""
    raise NotImplementedError("replaced by the HTTP layer at startup")
