"""Loans of books to members."""

import sqlite3


def overdue(db: sqlite3.Connection, today: str) -> list[int]:
    """Ids of loans past their due date."""
    query = "SELECT id FROM loans WHERE due < ? AND returned IS NULL"
    return [row[0] for row in db.execute(query, (today,))]
