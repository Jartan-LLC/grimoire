"""The records the leaguekit modules pass to one another."""

import datetime
import enum
from dataclasses import dataclass


class LeagueError(ValueError):
    """Input the season tools cannot work with, such as a duplicate team or an undecided tie."""


@dataclass(frozen=True)
class Team:
    """A team entered in the season.

    `code` is the team's unique short id, used in every file and table. `seed` is its
    1-based pre-season seed, lower is stronger; seeds are unique and stand in for the
    drawing of lots. `rating` is its Elo rating going into the season.
    """

    code: str
    name: str
    seed: int
    rating: float = 1500.0


@dataclass(frozen=True)
class Result:
    """The score of a played match.

    `home_goals` and `away_goals` include any goals scored in extra time; `extra_time`
    is True when extra time was played. `home_penalties` and `away_penalties` are the
    shoot-out score, both None when there was no shoot-out.
    """

    home_goals: int
    away_goals: int
    extra_time: bool = False
    home_penalties: int | None = None
    away_penalties: int | None = None


@dataclass(frozen=True)
class Match:
    """One fixture between two teams, named by code.

    `round` counts from 1. `date` is None until the fixture is dated, and `result` is
    None until it is played.
    """

    round: int
    home: str
    away: str
    date: datetime.date | None = None
    result: Result | None = None


@dataclass(frozen=True)
class StandingRow:
    """One team's line in a league table.

    `position` counts from 1. Teams the tiebreakers cannot tell apart share a position.
    """

    position: int
    team: str
    played: int
    won: int
    drawn: int
    lost: int
    goals_for: int
    goals_against: int
    goal_difference: int
    points: int


class TiebreakRule(enum.Enum):
    """One step of the chain that orders teams in a table."""

    POINTS = "points"
    HEAD_TO_HEAD = "head-to-head"
    GOAL_DIFFERENCE = "goal-difference"
    GOALS_FOR = "goals-for"
    AWAY_GOALS = "away-goals"
    FAIR_PLAY = "fair-play"
    LOT = "lot"


# The chain a table uses unless told otherwise.
DEFAULT_TIEBREAKERS = (
    TiebreakRule.POINTS,
    TiebreakRule.HEAD_TO_HEAD,
    TiebreakRule.GOAL_DIFFERENCE,
    TiebreakRule.GOALS_FOR,
    TiebreakRule.AWAY_GOALS,
    TiebreakRule.FAIR_PLAY,
    TiebreakRule.LOT,
)
