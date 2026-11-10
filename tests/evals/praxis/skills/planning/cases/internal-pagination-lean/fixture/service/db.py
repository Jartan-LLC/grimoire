import sqlite3

CONN = sqlite3.connect("orders.db", check_same_thread=False)
CONN.row_factory = sqlite3.Row


def all_orders():
    return [dict(r) for r in CONN.execute("SELECT * FROM orders ORDER BY created_at DESC")]
