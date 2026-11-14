import sqlite3

CONN = sqlite3.connect("shop.db", check_same_thread=False)
CONN.row_factory = sqlite3.Row


def orders_for(customer_id, month):
    return [dict(r) for r in CONN.execute(
        "SELECT * FROM orders WHERE customer_id = ? AND month = ?", (customer_id, month))]


def fetch_items(order_id):
    return [dict(r) for r in CONN.execute(
        "SELECT * FROM items WHERE order_id = ?", (order_id,))]
