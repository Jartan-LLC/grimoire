import dataclasses

import pytest

from transitkit import SECONDS_PER_DAY, ExceptionKind, Feed, StopTime


def test_an_empty_feed_has_no_records():
    feed = Feed()
    assert feed.stops == []
    assert feed.stop_times == []
    assert feed.exceptions == []


def test_a_stop_time_may_run_past_midnight():
    call = StopTime("t1", "central", 7, arrival=88800, departure=88860)
    assert call.arrival > SECONDS_PER_DAY
    with pytest.raises(dataclasses.FrozenInstanceError):
        call.arrival = 0  # type: ignore[misc]


def test_exception_kinds_use_the_gtfs_codes():
    assert ExceptionKind(1) is ExceptionKind.ADDED
    assert ExceptionKind(2) is ExceptionKind.REMOVED
