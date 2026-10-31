"""The library's open days, shared by every module that counts or moves dates."""

import datetime
from collections.abc import Collection

SUNDAY = 6


def is_open(day: datetime.date, closures: Collection[datetime.date] = ()) -> bool:
    """Whether the library is open on `day`: every day but Sunday, except closure days."""
    return day.weekday() != SUNDAY and day not in closures


def next_open(day: datetime.date, closures: Collection[datetime.date] = ()) -> datetime.date:
    """`day` itself if the library is open, otherwise the next open day after it."""
    while not is_open(day, closures):
        day += datetime.timedelta(days=1)
    return day


def add_open_days(
    day: datetime.date, count: int, closures: Collection[datetime.date] = ()
) -> datetime.date:
    """The `count`th open day after `day`."""
    for _ in range(count):
        day = next_open(day + datetime.timedelta(days=1), closures)
    return day
