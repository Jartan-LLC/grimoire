from service import create_app


def test_list_orders_returns_json(monkeypatch):
    order = {"id": 1, "customer": "c", "total": 5, "created_at": "2026-11-01"}
    monkeypatch.setattr("service.db.all_orders", lambda: [order])
    client = create_app().test_client()
    assert client.get("/internal/orders").get_json()[0]["id"] == 1
