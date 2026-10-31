"""ISBNs for books, unique where known."""


def up(conn):
    conn.execute("ALTER TABLE books ADD COLUMN isbn TEXT")
    conn.execute("CREATE UNIQUE INDEX books_isbn ON books (isbn) WHERE isbn IS NOT NULL")
