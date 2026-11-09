"""Books in the catalogue."""

import sqlite3


def by_author(db: sqlite3.Connection, author: str) -> list[str]:
    """Titles by `author`."""
    rows = db.execute("SELECT title FROM books WHERE author = ?", (author,))
    return [row[0] for row in rows]
