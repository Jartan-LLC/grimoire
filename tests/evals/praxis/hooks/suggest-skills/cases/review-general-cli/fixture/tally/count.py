"""Count first preferences."""

from collections import Counter


def first_preferences(ballots: list[list[str]]) -> Counter[str]:
    """How many ballots put each candidate first."""
    return Counter(ballot[0] for ballot in ballots if ballot)
