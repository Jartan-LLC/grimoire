"""Orders in the shop database."""

from shop.db import db


def mark_paid(reference):
    with db:
        db.execute("UPDATE orders SET status = 'paid' WHERE reference = ?", (reference,))


def get(reference):
    return db.execute("SELECT * FROM orders WHERE reference = ?", (reference,)).fetchone()
