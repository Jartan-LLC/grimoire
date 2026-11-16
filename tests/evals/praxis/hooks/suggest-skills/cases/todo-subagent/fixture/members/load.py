"""Read the office's member export: one `name,email,year joined` line per member."""

from collections.abc import Iterable
from dataclasses import dataclass


@dataclass(frozen=True)
class Member:
    """One club member."""

    name: str
    email: str
    joined: int


def parse_member(line: str) -> Member:
    """The member on `line`, such as `Ann Lee,ann@example.org,2019`."""
    name, email, joined = line.strip().split(",")
    if "@" not in email:
        raise ValueError(f"not an email address: {email!r}")
    return Member(name.strip(), email.strip(), int(joined))


def load_members(lines: Iterable[str]) -> list[Member]:
    """Every member in the export `lines`."""
    return [parse_member(line) for line in lines if line.strip()]
