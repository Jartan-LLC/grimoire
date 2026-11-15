"""Product search."""

from shop.db import db


def search(term):
    like = f"%{term}%"
    return db.execute("SELECT * FROM products WHERE name LIKE ? ORDER BY name", (like,)).fetchall()
