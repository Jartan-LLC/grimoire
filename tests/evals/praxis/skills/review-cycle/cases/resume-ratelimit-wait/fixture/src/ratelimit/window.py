"""A sliding-window rate limiter."""

import time

UNITS = {"s": 1, "m": 60}


def parse_window(text):
    """Return (limit, seconds) from a spec such as "10/m"."""
    count, unit = text.split("/")
    return int(count), UNITS[unit]


def prune_calls(calls, now, seconds):
    """The calls still inside the window that ends at `now`."""
    return [t for t in calls if now - t < seconds]


class SlidingWindow:
    """Allow at most `limit` calls in any `seconds`-long window."""

    def __init__(self, spec, clock=time.monotonic):
        self.limit, self.seconds = parse_window(spec)
        self.clock = clock
        self.calls = []

    def allow(self):
        """Record a call and say whether it is within the limit."""
        now = self.clock()
        self.calls = prune_calls(self.calls, now, self.seconds)
        if len(self.calls) >= self.limit:
            return False
        self.calls.append(now)
        return True
