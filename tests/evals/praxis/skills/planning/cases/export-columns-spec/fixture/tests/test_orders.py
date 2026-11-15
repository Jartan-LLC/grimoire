from export import orders


def test_rows(monkeypatch):
    order = {"id": 1, "customer": "c", "created_at": "2026-10-02", "total": 5}
    monkeypatch.setattr("export.db.orders_in", lambda month: [order])
    assert list(orders.rows("2026-10")) == [[1, "c", "2026-10-02", 5]]
