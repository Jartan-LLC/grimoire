import sqlite3

from shopdb.migrate import migrate


def test_migrations_run_once():
    conn = sqlite3.connect(":memory:")
    assert migrate(conn) == 3
    assert migrate(conn) == 0
    columns = [row[1] for row in conn.execute("PRAGMA table_info(customers)")]
    assert columns == ["id", "name", "email", "created_at"]
