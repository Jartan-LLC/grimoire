def create_user(conn, email, name):
    row = conn.execute(
        "INSERT INTO users (email, name) VALUES (%s, %s) RETURNING id", (email, name)
    ).fetchone()
    return row[0]


def change_email(conn, user_id, email):
    conn.execute("UPDATE users SET email = %s WHERE id = %s", (email, user_id))


def find_by_email(conn, email):
    return conn.execute(
        "SELECT id, email, name FROM users WHERE email = %s", (email,)
    ).fetchone()
