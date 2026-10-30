"""The interface every backend implements."""

from abc import ABC, abstractmethod
from collections.abc import Iterator


class Store(ABC):
    @abstractmethod
    def get(self, key: str) -> bytes | None: ...

    @abstractmethod
    def set(self, key: str, value: bytes, ttl: float | None = None) -> None: ...

    @abstractmethod
    def delete(self, key: str) -> bool: ...

    @abstractmethod
    def keys(self) -> Iterator[str]: ...
