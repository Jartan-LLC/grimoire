"""Parse durations like "1h30m"."""

import re

_PART = re.compile(r"(\d+)([hms])")
_WHOLE = re.compile(r"(\d+[hms])+")


def parse_duration(text: str) -> int:
    """Seconds in a duration such as "1h30m" or "45s"; ValueError for anything else."""
    if not _WHOLE.fullmatch(text):
        raise ValueError(text)
    seconds = 0
    for amount, unit in _PART.findall(text):
        seconds += int(amount) * {"h": 3600, "m": 60, "s": 1}[unit]
    return seconds
