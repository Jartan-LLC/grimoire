"""The HTTP handlers."""

from app.db import connect


def list_notes() -> list[str]:
    """Every note's title."""
    return [row[0] for row in connect().execute("SELECT title FROM notes")]
