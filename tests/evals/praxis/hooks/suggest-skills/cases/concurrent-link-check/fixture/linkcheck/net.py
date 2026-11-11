"""Ask a server whether a link is alive."""

import asyncio

# Stands in for the HTTP client here: the time a real server takes to answer.
LATENCY_S = 0.05


async def head(url: str) -> int:
    """The status code a HEAD request to `url` gets."""
    await asyncio.sleep(LATENCY_S)
    return 404 if url.endswith("/gone") else 200
