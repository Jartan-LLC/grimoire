from notekit.store import Store


def test_ids_count_up():
    store = Store()
    assert [store.add("a", set()).id, store.add("b", set()).id] == [1, 2]
