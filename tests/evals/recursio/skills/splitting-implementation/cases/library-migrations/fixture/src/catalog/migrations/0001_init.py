"""Books and members."""


def up(conn):
    conn.execute(
        "CREATE TABLE books (id INTEGER PRIMARY KEY, title TEXT NOT NULL, author TEXT NOT NULL)"
    )
    conn.execute(
        "CREATE TABLE members (id INTEGER PRIMARY KEY, name TEXT NOT NULL, "
        "tier TEXT NOT NULL DEFAULT 'standard')"
    )
