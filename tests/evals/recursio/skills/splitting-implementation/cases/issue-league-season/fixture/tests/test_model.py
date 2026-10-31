import dataclasses

import pytest

from leaguekit import DEFAULT_TIEBREAKERS, Match, Result, TiebreakRule


def test_a_result_has_no_extra_time_or_shoot_out_by_default():
    r = Result(2, 1)
    assert r.extra_time is False
    assert r.home_penalties is None and r.away_penalties is None


def test_a_match_starts_undated_and_unplayed():
    m = Match(1, "ANT", "BEE")
    assert m.date is None and m.result is None
    with pytest.raises(dataclasses.FrozenInstanceError):
        m.round = 2  # type: ignore[misc]


def test_the_default_chain_starts_with_points_and_ends_with_the_lot():
    assert DEFAULT_TIEBREAKERS[0] is TiebreakRule.POINTS
    assert DEFAULT_TIEBREAKERS[-1] is TiebreakRule.LOT
