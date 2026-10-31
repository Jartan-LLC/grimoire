def up(conn):
    conn.execute("ALTER TABLE customers ADD COLUMN created_at TEXT")
