"""The contact every reader returns."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Contact:
    """One person."""

    name: str
    email: str | None = None
    phone: str | None = None
