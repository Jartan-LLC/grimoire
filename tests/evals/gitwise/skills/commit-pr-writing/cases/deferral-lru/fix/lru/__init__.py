"""A small least-recently-used cache."""

from collections import OrderedDict


class LRUCache:
    """Keeps at most `capacity` items, dropping the least recently used."""

    def __init__(self, capacity: int) -> None:
        self.capacity = capacity
        self.items: OrderedDict[str, object] = OrderedDict()

    def put(self, key: str, value: object) -> None:
        """Store `value` under `key`."""
        self.items[key] = value
        self.items.move_to_end(key)
        if len(self.items) > self.capacity:
            self.items.popitem(last=False)
