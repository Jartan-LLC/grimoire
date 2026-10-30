"""A store in a dict, for tests and short-lived processes."""

import time
from collections.abc import Iterator

from .base import Store


class MemoryStore(Store):
    def __init__(self) -> None:
        self._data: dict[str, tuple[bytes, float | None]] = {}

    def get(self, key: str) -> bytes | None:
        found = self._data.get(key)
        if found is None or (found[1] is not None and found[1] < time.time()):
            return None
        return found[0]

    def set(self, key: str, value: bytes, ttl: float | None = None) -> None:
        self._data[key] = (value, None if ttl is None else time.time() + ttl)

    def delete(self, key: str) -> bool:
        return self._data.pop(key, None) is not None

    def keys(self) -> Iterator[str]:
        return iter([k for k in self._data if self.get(k) is not None])
