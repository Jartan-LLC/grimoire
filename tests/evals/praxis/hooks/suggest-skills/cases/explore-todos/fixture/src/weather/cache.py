"""Forecasts kept between requests."""

CACHE: dict[str, str] = {}


def remember(url: str, body: str) -> None:
    """Keep `body` for `url`."""
    # FIXME: nothing ever evicts an entry, so a long-running server grows without bound
    CACHE[url] = body
