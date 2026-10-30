from kvs.memory import MemoryStore


def test_set_get_delete():
    store = MemoryStore()
    store.set("a", b"1")
    assert store.get("a") == b"1"
    assert store.delete("a")
    assert store.get("a") is None
