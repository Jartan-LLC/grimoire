# SPDX-License-Identifier: MIT
"""Acceptance tests for votekit, as the README specifies."""

import json

import pytest

from votekit.ballots import parse_ballots
from votekit.cli import main
from votekit.irv import instant_runoff
from votekit.model import Ballot, BallotError, Result, Round
from votekit.plurality import plurality
from votekit.render import render_json, render_text

NAMES = ["Ada", "Bo", "Cy"]
BALLOTS = """# club vote
v1: Ada > Bo
v2: Ada > Cy
v3: Bo > Cy > Ada
v4: Bo > Ada
v5: Cy > Bo
v6: Ada
v7: Bo > Cy
"""
RUNOFF = Result(
    "Bo",
    [Round({"Ada": 3, "Bo": 3, "Cy": 1}, "Cy"), Round({"Ada": 3, "Bo": 4}, None)],
)
TEXT = "Round 1: Ada 3, Bo 3, Cy 1 -- Cy out\nRound 2: Bo 4, Ada 3\nWinner: Bo\n"


def test_ballots_parse_in_file_order():
    ballots = parse_ballots(BALLOTS, NAMES)
    assert len(ballots) == 7
    assert ballots[0] == Ballot("v1", ("Ada", "Bo"))
    assert ballots[5] == Ballot("v6", ("Ada",))


def test_ballots_name_the_bad_line():
    with pytest.raises(BallotError, match=r"^line 2: "):
        parse_ballots("v1: Ada\nv2: Zed\n", NAMES)


def test_plurality_tie_has_no_winner():
    assert plurality(parse_ballots(BALLOTS, NAMES), NAMES) == Result(None, [Round({"Ada": 3, "Bo": 3, "Cy": 1}, None)])


def test_runoff_transfers_the_eliminated_candidates_ballots():
    assert instant_runoff(parse_ballots(BALLOTS, NAMES), NAMES) == RUNOFF


def test_runoff_majority_is_of_counted_ballots():
    ballots = parse_ballots("x1: Ada\nx2: Ada\nx3: Ada\nx4: Bo\nx5: Bo\nx6: Cy\n", NAMES)
    assert instant_runoff(ballots, NAMES) == Result(
        "Ada", [Round({"Ada": 3, "Bo": 2, "Cy": 1}, "Cy"), Round({"Ada": 3, "Bo": 2}, None)]
    )


def test_runoff_counts_zeros():
    ballots = parse_ballots("x1: Ada\nx2: Ada\nx3: Bo\n", NAMES)
    assert instant_runoff(ballots, NAMES).rounds[0] == Round({"Ada": 2, "Bo": 1, "Cy": 0}, None)


def test_render_text():
    assert render_text(RUNOFF) == TEXT
    assert render_text(Result(None, [Round({"Bo": 3, "Ada": 3, "Cy": 1}, None)])) == "Round 1: Ada 3, Bo 3, Cy 1\nNo winner\n"


def test_render_json():
    data = json.loads(render_json(RUNOFF))
    assert list(data) == ["winner", "rounds"]
    assert data == {
        "winner": "Bo",
        "rounds": [
            {"counts": {"Ada": 3, "Bo": 3, "Cy": 1}, "eliminated": "Cy"},
            {"counts": {"Ada": 3, "Bo": 4}, "eliminated": None},
        ],
    }


@pytest.fixture
def path(tmp_path):
    target = tmp_path / "ballots.txt"
    target.write_text(BALLOTS)
    return target


def test_cli_counts_by_runoff(path, capsys):
    assert main(["count", str(path), "--candidates", "Ada,Bo,Cy"]) == 0
    assert capsys.readouterr().out == TEXT


def test_cli_plurality_without_winner_exits_1(path, capsys):
    assert main(["count", str(path), "--candidates", "Ada,Bo,Cy", "--method", "plurality"]) == 1
    assert capsys.readouterr().out == "Round 1: Ada 3, Bo 3, Cy 1\nNo winner\n"


def test_cli_json(path, capsys):
    assert main(["count", str(path), "--candidates", "Ada,Bo,Cy", "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["winner"] == "Bo"


def test_cli_bad_ballot_exits_2(tmp_path, capsys):
    bad = tmp_path / "ballots.txt"
    bad.write_text("v1: Ada\nv2: Zed\n")
    assert main(["count", str(bad), "--candidates", "Ada,Bo,Cy"]) == 2
    assert capsys.readouterr().err.startswith("votekit: line 2: ")
