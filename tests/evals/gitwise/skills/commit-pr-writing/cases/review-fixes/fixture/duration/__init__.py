"""Parse durations like "1h30m"."""

import re

_PART = re.compile(r"(\d+)([hms])")


def parse_duration(text: str) -> int:
    """Seconds in a duration such as "1h30m" or "45s"."""
    secs = 0
    for amount, unit in _PART.findall(text):
        secs += int(amount) * {"h": 3600, "m": 60, "s": 1}[unit]
    return secs
