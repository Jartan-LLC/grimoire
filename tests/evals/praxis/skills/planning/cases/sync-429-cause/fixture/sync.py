import sqlite3

from client import fetch_page

PAGE_SIZE = 100


def sync(db_path="orders.db"):
    db = sqlite3.connect(db_path)
    page = 1
    while True:
        orders = fetch_page(page, PAGE_SIZE)
        if not orders:
            break
        db.executemany("INSERT OR REPLACE INTO orders VALUES (?, ?)",
                       [(o["id"], o["total"]) for o in orders])
        page += 1
    db.commit()


if __name__ == "__main__":
    sync()
