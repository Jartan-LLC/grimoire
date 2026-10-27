"""Fetch a resource, retrying transient failures."""

from fetchkit import transport
from fetchkit.retry import with_retries
from fetchkit.transport import Response


def get(url: str) -> Response:
    """GET `url`, retrying 5xx responses."""
    return with_retries(lambda: transport.send(url))
