from report.totals import month_total

ORDERS = [{"month": "2026-10", "amount": 60}, {"month": "2026-10", "amount": 40}]


def test_october_total():
    assert month_total(ORDERS, "2026-10") == 100
