"""Apply each migrations/*.sql not yet recorded, in name order, each in one transaction."""
import os
import pathlib

import psycopg


def main():
    with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS schema_migrations (name text PRIMARY KEY)")
        done = {r[0] for r in conn.execute("SELECT name FROM schema_migrations")}
        for path in sorted(pathlib.Path("migrations").glob("*.sql")):
            if path.name in done:
                continue
            with conn.transaction():
                conn.execute(path.read_text())
                conn.execute("INSERT INTO schema_migrations VALUES (%s)", (path.name,))


if __name__ == "__main__":
    main()
