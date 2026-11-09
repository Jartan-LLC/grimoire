"""Upload what changed locally."""

import time
import urllib.request


def push(url: str, body: bytes) -> None:
    """PUT `body` to `url`, retrying while the server is busy."""
    tries = 0
    while True:
        try:
            urllib.request.urlopen(urllib.request.Request(url, body, method="PUT"), timeout=10)
            return
        except OSError:
            tries += 1
            if tries == 5:
                raise
            time.sleep(1)
