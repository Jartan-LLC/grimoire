def digest_recipients(conn):
    rows = conn.execute("SELECT id, email FROM users WHERE marketing_opt_in ORDER BY id")
    return [{"id": r[0], "email": r[1]} for r in rows]
