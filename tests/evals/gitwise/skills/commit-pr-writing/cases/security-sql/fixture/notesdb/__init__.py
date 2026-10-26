"""Search notes in SQLite."""

import sqlite3


def find_notes(db: sqlite3.Connection, owner: str, text: str) -> list[str]:
    """Bodies of `owner`'s notes that contain `text`."""
    sql = f"SELECT body FROM notes WHERE owner = '{owner}' AND body LIKE '%{text}%'"
    return [row[0] for row in db.execute(sql)]
