from stockroom.store import Store


def test_put_then_get():
    store = Store()
    store.put("A-1", 3)
    assert store.get("A-1") == 3
