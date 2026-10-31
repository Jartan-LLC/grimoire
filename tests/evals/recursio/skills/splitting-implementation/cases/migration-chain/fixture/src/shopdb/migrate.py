"""Apply the numbered migrations a database has not run yet."""

import importlib.util
import pathlib
import sqlite3

MIGRATIONS = pathlib.Path(__file__).resolve().parent / "migrations"


def pending(conn: sqlite3.Connection) -> list[pathlib.Path]:
    """The migration files numbered above the highest version the database has run."""
    conn.execute("CREATE TABLE IF NOT EXISTS schema_version (version INTEGER NOT NULL)")
    done = conn.execute("SELECT MAX(version) FROM schema_version").fetchone()[0] or 0
    found = sorted(MIGRATIONS.glob("[0-9][0-9][0-9][0-9]_*.py"))
    return [p for p in found if int(p.name[:4]) > done]


def migrate(conn: sqlite3.Connection) -> int:
    """Run every pending migration in order; return how many ran."""
    ran = 0
    for path in pending(conn):
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        module.up(conn)
        conn.execute("INSERT INTO schema_version (version) VALUES (?)", (int(path.name[:4]),))
        conn.commit()
        ran += 1
    return ran
