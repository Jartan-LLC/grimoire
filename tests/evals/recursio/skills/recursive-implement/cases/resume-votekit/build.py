"""Build this case's history: run by the eval runner inside the fixture repository.

A walk-away run that stopped after its first wave: the shared types, both wave 1 parts with their
tests, and split.md recording wave 1 passed and waves 2 and 3 pending, all left uncommitted.
"""

import pathlib

FILES = {
    "src/votekit/__init__.py": r'''# SPDX-License-Identifier: MIT
"""votekit: count ranked ballots."""
''',
    "src/votekit/model.py": r'''# SPDX-License-Identifier: MIT
"""Shared types for votekit: ballots, rounds and results."""

from dataclasses import dataclass


class BallotError(ValueError):
    """A ballot file that cannot be read."""


@dataclass(frozen=True)
class Ballot:
    voter: str
    ranking: tuple[str, ...]


@dataclass(frozen=True)
class Round:
    counts: dict[str, int]
    eliminated: str | None


@dataclass(frozen=True)
class Result:
    winner: str | None
    rounds: list[Round]
''',
    "src/votekit/ballots.py": r'''# SPDX-License-Identifier: MIT
"""Parse a ballot file."""

from votekit.model import Ballot, BallotError


def parse_ballots(text: str, candidates: list[str]) -> list[Ballot]:
    """The ballots in file order; BallotError names the line of the first bad one."""
    ballots: list[Ballot] = []
    voters: set[str] = set()
    for number, line in enumerate(text.splitlines(), start=1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        voter, colon, rest = line.partition(":")
        voter = voter.strip()
        if not colon or not voter:
            raise BallotError(f"line {number}: expected 'voter: A > B'")
        ranking = tuple(name.strip() for name in rest.split(">") if name.strip())
        for name in ranking:
            if name not in candidates:
                raise BallotError(f"line {number}: unknown candidate {name!r}")
        if len(set(ranking)) != len(ranking):
            raise BallotError(f"line {number}: a candidate is ranked twice")
        if voter in voters:
            raise BallotError(f"line {number}: voter {voter!r} has already voted")
        voters.add(voter)
        ballots.append(Ballot(voter, ranking))
    return ballots
''',
    "src/votekit/plurality.py": r'''# SPDX-License-Identifier: MIT
"""Count first choices."""

from votekit.model import Ballot, Result, Round


def plurality(ballots: list[Ballot], candidates: list[str]) -> Result:
    """One round of first choices; a tie for the most has no winner."""
    counts = dict.fromkeys(candidates, 0)
    for ballot in ballots:
        if ballot.ranking:
            counts[ballot.ranking[0]] += 1
    most = max(counts.values(), default=0)
    leaders = [name for name, votes in counts.items() if votes == most]
    winner = leaders[0] if len(leaders) == 1 and most > 0 else None
    return Result(winner, [Round(counts, None)])
''',
    "tests/test_ballots.py": r'''# SPDX-License-Identifier: MIT
"""Tests for votekit.ballots."""

import pytest

from votekit.ballots import parse_ballots
from votekit.model import Ballot, BallotError

NAMES = ["Ada", "Bo", "Cy"]


def test_rankings_in_file_order():
    text = "# a comment\n\nv1: Ada > Cy\nv2: Bo\n"
    assert parse_ballots(text, NAMES) == [Ballot("v1", ("Ada", "Cy")), Ballot("v2", ("Bo",))]


def test_empty_ranking_is_kept():
    assert parse_ballots("v1:\n", NAMES) == [Ballot("v1", ())]


@pytest.mark.parametrize(
    ("text", "line"),
    [
        ("v1: Ada\nno colon here\n", 2),
        ("v1: Zed\n", 1),
        ("v1: Ada > Ada\n", 1),
        ("v1: Ada\n\nv1: Bo\n", 3),
        (": Ada\n", 1),
    ],
)
def test_bad_lines_name_their_line(text, line):
    with pytest.raises(BallotError, match=rf"^line {line}: "):
        parse_ballots(text, NAMES)
''',
    "tests/test_plurality.py": r'''# SPDX-License-Identifier: MIT
"""Tests for votekit.plurality."""

from votekit.model import Ballot, Result, Round
from votekit.plurality import plurality

NAMES = ["Ada", "Bo", "Cy"]


def test_most_first_choices_wins():
    ballots = [Ballot("v1", ("Bo", "Ada")), Ballot("v2", ("Bo",)), Ballot("v3", ("Ada",))]
    assert plurality(ballots, NAMES) == Result("Bo", [Round({"Ada": 1, "Bo": 2, "Cy": 0}, None)])


def test_tie_for_most_has_no_winner():
    ballots = [Ballot("v1", ("Bo",)), Ballot("v2", ("Ada",)), Ballot("v3", ())]
    assert plurality(ballots, NAMES).winner is None


def test_no_ballots_has_no_winner():
    assert plurality([], NAMES) == Result(None, [Round({"Ada": 0, "Bo": 0, "Cy": 0}, None)])
''',
    ".claude/workspace/votekit/split.md": r"""If the splitting skill was lost to compaction, load `recursio:splitting-implementation` again and resume from the status lines below.

# Split: votekit

## Settled decisions

- Shared types in `src/votekit/model.py`: `Ballot`, `Round`, `Result` and `BallotError` -- source: the README.
- Each module's own tests in `tests/test_<module>.py`, run with `python3 -m pytest -q tests/test_<module>.py` -- source: decided here.
- Every `counts` dict lists candidates in the order of `candidates` -- source: decided here.

## Wave 1

Snapshot before spawning: no changed files; contract hashes: src/votekit/model.py 4874d7117d2f0546d09735b01609970355b614b5

### ballots

- Owns: src/votekit/ballots.py, tests/test_ballots.py
- Depends on: src/votekit/model.py
- Contract: src/votekit/model.py
- Contract tests: tests/test_acceptance.py, run with `python3 -m pytest -q tests/test_acceptance.py -k ballots`
- Agent type: general-purpose
- Status: passed
- Outcome: built

### plurality

- Owns: src/votekit/plurality.py, tests/test_plurality.py
- Depends on: src/votekit/model.py
- Contract: src/votekit/model.py
- Contract tests: tests/test_acceptance.py, run with `python3 -m pytest -q tests/test_acceptance.py -k plurality`
- Agent type: general-purpose
- Status: passed
- Outcome: built

### Barrier

Scope: every changed file lies in one part's scope; model.py matches its hash. `python3 -m pytest -q tests/test_ballots.py tests/test_plurality.py`: 10 passed. `python3 -m pytest -q tests/test_acceptance.py -k "ballots or plurality"`: not run, as the acceptance tests import modules of later waves. No divergence; no retries.

## Wave 2

### irv

- Owns: src/votekit/irv.py, tests/test_irv.py
- Depends on: src/votekit/model.py
- Contract: src/votekit/model.py
- Contract tests: tests/test_acceptance.py, run with `python3 -m pytest -q tests/test_acceptance.py -k runoff`
- Agent type: general-purpose
- Status: pending
- Outcome:

### render

- Owns: src/votekit/render.py, tests/test_render.py
- Depends on: src/votekit/model.py
- Contract: src/votekit/model.py
- Contract tests: tests/test_acceptance.py, run with `python3 -m pytest -q tests/test_acceptance.py -k render`
- Agent type: general-purpose
- Status: pending
- Outcome:

### Barrier

Not run yet.

## Wave 3

### cli

- Owns: src/votekit/cli.py, tests/test_cli.py
- Depends on: ballots, plurality, irv, render
- Contract: the README's Command section
- Contract tests: tests/test_acceptance.py, run with `python3 -m pytest -q tests/test_acceptance.py -k cli`
- Agent type: general-purpose
- Status: pending
- Outcome:

### Barrier

Not run yet.

## Decided without asking

- Every `counts` dict lists candidates in the order of `candidates` -- the README does not say.

## Left for the user
""",
}

for name, text in FILES.items():
    target = pathlib.Path(name)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text)
