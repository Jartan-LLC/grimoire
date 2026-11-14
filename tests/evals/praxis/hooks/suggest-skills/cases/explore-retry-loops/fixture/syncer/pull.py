"""Download what changed on the server."""

import time
import urllib.request


def pull(url: str) -> bytes:
    """The body at `url`, trying up to three times."""
    for attempt in range(3):
        try:
            with urllib.request.urlopen(url, timeout=10) as response:
                return response.read()
        except OSError:
            time.sleep(2**attempt)
    raise OSError(f"gave up on {url}")
