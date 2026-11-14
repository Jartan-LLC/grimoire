from datetime import datetime

from remindme.add import add_reminder
from remindme.store import load


def test_due_in_minutes(tmp_path):
    path = tmp_path / "r.json"
    item = add_reminder(path, "Call the dentist", 90, datetime(2026, 11, 3, 9, 0))
    assert item == {"id": 1, "text": "Call the dentist", "due": "2026-11-03T10:30"}
    assert load(path) == [item]
