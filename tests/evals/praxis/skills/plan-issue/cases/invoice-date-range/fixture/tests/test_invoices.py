from clinicdesk.invoices import list_invoices


def test_oldest_first():
    assert [i["number"] for i in list_invoices({})] == ["2026-101", "2026-102", "2026-103"]
