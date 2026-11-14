import os

import psycopg


def query(sql, params=()):
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        return conn.execute(sql, params).fetchall()
