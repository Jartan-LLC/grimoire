"""Search notes in SQLite."""

import sqlite3


def find_notes(db: sqlite3.Connection, owner: str, text: str) -> list[str]:
    """Bodies of `owner`'s notes that contain `text`."""
    sql = "SELECT body FROM notes WHERE owner = ? AND body LIKE ?"
    return [row[0] for row in db.execute(sql, (owner, f"%{text}%"))]
