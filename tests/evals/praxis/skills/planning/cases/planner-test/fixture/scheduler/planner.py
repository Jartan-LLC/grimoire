"""Meeting slots."""

from datetime import timedelta


def next_slot(busy, start, length):
    """The first start time at or after `start` that overlaps no (begin, end) in `busy`."""
    slot = start
    for begin, end in sorted(busy):
        if slot + length <= begin:
            break
        slot = max(slot, end)
    return slot


HOUR = timedelta(hours=1)
