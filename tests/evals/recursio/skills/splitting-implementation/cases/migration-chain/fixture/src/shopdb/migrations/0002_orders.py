def up(conn):
    conn.execute(
        "CREATE TABLE orders (id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(id), total_cents INTEGER)"
    )
