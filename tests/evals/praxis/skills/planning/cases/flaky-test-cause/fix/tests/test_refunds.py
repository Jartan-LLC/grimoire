from report.totals import month_total

ORDERS = [{"month": "2026-10", "amount": 60}, {"month": "2026-10", "amount": 30}]


def test_total_after_a_refund():
    assert month_total(ORDERS, "2026-10") == 90
