"""Loans: a book out to a member from `loaned_at` until it is returned."""


def up(conn):
    conn.execute(
        "CREATE TABLE loans ("
        "id INTEGER PRIMARY KEY, "
        "book_id INTEGER NOT NULL REFERENCES books(id), "
        "member_id INTEGER NOT NULL REFERENCES members(id), "
        "loaned_at TEXT NOT NULL, "
        "returned_at TEXT)"
    )
