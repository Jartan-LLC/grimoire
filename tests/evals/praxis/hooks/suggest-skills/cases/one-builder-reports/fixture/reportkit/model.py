"""The table every format renders."""

from dataclasses import dataclass

type Cell = str | int | float | None


@dataclass(frozen=True)
class Table:
    """A header and rows of the same width."""

    header: list[str]
    rows: list[list[Cell]]
