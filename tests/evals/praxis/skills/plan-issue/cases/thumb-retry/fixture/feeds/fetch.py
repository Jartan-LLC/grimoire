"""Download a feed's XML."""

import time
import urllib.error
import urllib.request

ATTEMPTS = 3
BACKOFF_S = 1.0


def fetch_feed(url: str, timeout: float = 10.0) -> bytes:
    """The feed's XML, retried on network errors and 5xx answers with a growing pause."""
    for attempt in range(1, ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(url, timeout=timeout) as response:
                return response.read()
        except urllib.error.HTTPError as error:
            if error.code < 500 or attempt == ATTEMPTS:
                raise
        except urllib.error.URLError:
            if attempt == ATTEMPTS:
                raise
        time.sleep(BACKOFF_S * attempt)
    raise AssertionError("unreachable")
