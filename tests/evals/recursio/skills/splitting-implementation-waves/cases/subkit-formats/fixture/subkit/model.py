"""Shared types for every subkit module."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Cue:
    """One subtitle on screen from `start` to `end`, in milliseconds.

    `text` holds its lines joined by "\\n". The only markup kept is `<i>`, `<b>` and `<u>`,
    each closed on the line it opens on. `speaker` is who says it, when the format names one;
    `top` is True when the cue is shown at the top of the picture instead of the bottom.
    """

    start: int
    end: int
    text: str
    speaker: str | None = None
    top: bool = False


@dataclass(frozen=True)
class Skipped:
    """A record left out of a parse: the 1-based line it starts on and why."""

    line: int
    reason: str


@dataclass
class ParseResult:
    """What a format's parser hands back: the good cues, the records it skipped, and the title."""

    cues: list[Cue] = field(default_factory=list)
    skipped: list[Skipped] = field(default_factory=list)
    title: str | None = None


class FormatError(Exception):
    """The input is not in the format, or is broken beyond one record."""
