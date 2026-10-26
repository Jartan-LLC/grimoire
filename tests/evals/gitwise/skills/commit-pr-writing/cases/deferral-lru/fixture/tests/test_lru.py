from lru import LRUCache


def test_put() -> None:
    c = LRUCache(2)
    c.put('a', 1)
    assert c.items['a'] == 1
