"""Planted acceptance tests for the timing tools."""

import pytest

from subkit import Cue
from subkit.timing import merge, problems, retime, shift, sync


def test_shift_retime_and_sync():
    cues = [Cue(2000, 3000, "b"), Cue(500, 1500, "a"), Cue(100, 400, "gone")]
    assert shift(cues, -1000) == [Cue(0, 500, "a"), Cue(1000, 2000, "b")]
    assert retime([Cue(1001, 2002, "x")], 25, 23.976) == [Cue(1044, 2088, "x")]
    assert sync([Cue(1000, 2000, "x"), Cue(11000, 12000, "y")], (1000, 1500), (11000, 12500)) == [
        Cue(1500, 2600, "x"), Cue(12500, 13600, "y"),
    ]
    with pytest.raises(ValueError):
        sync(cues, (1000, 0), (1000, 5))


def test_problems_and_merge():
    cues = [
        Cue(0, 2000, "Hello"),
        Cue(1500, 2000, "<i>This line is far too long to read</i>"),
        Cue(5000, 6000, "Again"),
        Cue(6000, 7000, "Again"),
    ]
    assert problems(cues) == [(1, "overlap"), (1, "short"), (1, "fast")]
    assert merge(cues) == [cues[0], cues[1], Cue(5000, 7000, "Again")]
