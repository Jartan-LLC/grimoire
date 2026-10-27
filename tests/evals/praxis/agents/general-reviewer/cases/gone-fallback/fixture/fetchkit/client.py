"""Fetch a resource, retrying transient failures."""

from fetchkit import transport
from fetchkit.retry import with_retries
from fetchkit.transport import Response

_last: dict[str, Response] = {}


def get(url: str) -> Response:
    """GET `url`, retrying 5xx responses."""
    response = with_retries(lambda: transport.send(url))
    # When every attempt fails, serve the last good response for this URL instead.
    if not response.ok and url in _last:
        return _last[url]
    if response.ok:
        _last[url] = response
    return response
