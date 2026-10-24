import sqlite3

from notesdb import find_notes


def test_finds() -> None:
    db = sqlite3.connect(":memory:")
    db.execute("CREATE TABLE notes (owner TEXT, body TEXT)")
    db.execute("INSERT INTO notes VALUES ('ana', 'buy milk')")
    assert find_notes(db, "ana", "milk") == ["buy milk"]
