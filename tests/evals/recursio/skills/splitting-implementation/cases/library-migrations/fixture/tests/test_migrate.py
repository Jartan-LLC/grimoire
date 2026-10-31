import sqlite3

import pytest

from catalog.migrate import migrate


@pytest.fixture
def conn():
    connection = sqlite3.connect(":memory:")
    yield connection
    connection.close()


def columns(conn, table):
    return [row[1] for row in conn.execute(f"PRAGMA table_info({table})")]


def test_migrations_run_in_order_and_once(conn):
    assert migrate(conn) == [1, 2, 3, 4]
    assert migrate(conn) == []


def test_schema_after_migrating(conn):
    migrate(conn)
    assert columns(conn, "books") == ["id", "title", "author", "isbn"]
    assert columns(conn, "loans") == ["id", "book_id", "member_id", "loaned_at", "returned_at"]
    assert dict(conn.execute("SELECT name, loan_days FROM tiers")) == {
        "standard": 21,
        "student": 28,
        "staff": 42,
    }


def test_isbn_is_unique_when_given(conn):
    migrate(conn)
    conn.execute("INSERT INTO books (title, author) VALUES ('A', 'X'), ('B', 'Y')")
    conn.execute("INSERT INTO books (title, author, isbn) VALUES ('C', 'Z', '978-0')")
    with pytest.raises(sqlite3.IntegrityError):
        conn.execute("INSERT INTO books (title, author, isbn) VALUES ('D', 'Z', '978-0')")
