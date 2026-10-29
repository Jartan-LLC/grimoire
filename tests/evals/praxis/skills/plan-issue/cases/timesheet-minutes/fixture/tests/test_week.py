from timesheet.week import weekly_totals


def test_totals_by_iso_week():
    rows = [
        {"date": "2026-10-19", "project": "atlas", "hours": "7.5"},
        {"date": "2026-10-20", "project": "atlas", "hours": "8"},
        {"date": "2026-10-26", "project": "kite", "hours": "4.25"},
    ]
    assert weekly_totals(rows) == {"2026-W43": 15.5, "2026-W44": 4.25}
