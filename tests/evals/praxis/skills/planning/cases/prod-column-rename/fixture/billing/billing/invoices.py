def invoice_recipient(conn, user_id):
    return conn.execute("SELECT email FROM users WHERE id = %s", (user_id,)).fetchone()[0]
