"""Retry a call, backing off between attempts."""

import random
import time
from collections.abc import Callable


def retry(
    call: Callable[[], object],
    attempts: int = 3,
    base: float = 0.1,
    sleep: Callable[[float], None] = time.sleep,
) -> object:
    """`call()`, retried up to `attempts` more times on an exception.

    Waits `base * 2**n` seconds before retry n, plus up to one second of jitter.
    """
    tries = 0
    while True:
        try:
            return call()
        except Exception:
            tries += 1
            if attempts and tries > attempts:
                raise
            sleep(base * 2**tries + random.random())
