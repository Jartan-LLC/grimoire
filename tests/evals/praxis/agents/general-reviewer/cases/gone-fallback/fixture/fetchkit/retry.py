"""Retry a request that failed for a reason that may pass."""

import time
from collections.abc import Callable

from fetchkit.transport import Response

MAX_ATTEMPTS = 3
BASE_DELAY_S = 0.5


def with_retries(call: Callable[[], Response], sleep: Callable[[float], None] = time.sleep) -> Response:
    """`call()`, retried with exponential backoff while it fails with a 5xx status."""
    response = call()
    for attempt in range(1, MAX_ATTEMPTS):
        if response.status < 500:
            return response
        sleep(BASE_DELAY_S * 2 ** (attempt - 1))
        response = call()
    return response
