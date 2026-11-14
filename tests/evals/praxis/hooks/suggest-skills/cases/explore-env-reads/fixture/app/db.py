"""The database connection."""

import os
import sqlite3


def connect() -> sqlite3.Connection:
    """A connection to the notes database."""
    return sqlite3.connect(os.environ.get("NOTES_DB_PATH", "notes.db"))
