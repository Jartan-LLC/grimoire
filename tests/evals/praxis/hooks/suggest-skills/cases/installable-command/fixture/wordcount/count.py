"""The counts for one text."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Counts:
    """Lines, words and characters."""

    lines: int
    words: int
    chars: int


def count(text: str) -> Counts:
    """The counts for `text`."""
    return Counts(text.count("\n"), len(text.split()), len(text))
