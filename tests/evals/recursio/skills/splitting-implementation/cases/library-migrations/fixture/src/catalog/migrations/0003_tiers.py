"""Membership tiers and how many days each one's loans last."""

TIERS = [("standard", 21), ("student", 28), ("staff", 42)]


def up(conn):
    conn.execute("CREATE TABLE tiers (name TEXT PRIMARY KEY, loan_days INTEGER NOT NULL)")
    conn.executemany("INSERT INTO tiers (name, loan_days) VALUES (?, ?)", TIERS)
