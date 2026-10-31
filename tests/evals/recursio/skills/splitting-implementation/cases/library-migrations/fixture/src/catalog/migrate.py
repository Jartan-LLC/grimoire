"""Run the numbered migrations a database has not run yet, each in its own transaction."""

import importlib.util
import pathlib
import re
import sqlite3

MIGRATIONS = pathlib.Path(__file__).resolve().parent / "migrations"
NAME = re.compile(r"(\d{4})_\w+\.py")


def applied(conn: sqlite3.Connection) -> set[int]:
    """The migration numbers recorded as run."""
    conn.execute("CREATE TABLE IF NOT EXISTS applied_migrations (number INTEGER PRIMARY KEY)")
    return {row[0] for row in conn.execute("SELECT number FROM applied_migrations")}


def available() -> list[tuple[int, pathlib.Path]]:
    """Every migration file, by number."""
    found = []
    for path in MIGRATIONS.iterdir():
        if m := NAME.fullmatch(path.name):
            found.append((int(m.group(1)), path))
    return sorted(found)


def migrate(conn: sqlite3.Connection) -> list[int]:
    """Run every migration not yet applied, in number order; return the numbers run."""
    done = applied(conn)
    ran = []
    for number, path in available():
        if number in done:
            continue
        spec = importlib.util.spec_from_file_location(f"catalog_migration_{number}", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with conn:
            module.up(conn)
            conn.execute("INSERT INTO applied_migrations (number) VALUES (?)", (number,))
        ran.append(number)
    return ran
