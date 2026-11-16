"""Read the office's member export: one `name,email,year joined` line per member."""

from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Member:
    """One club member."""

    name: str
    email: str
    joined: int


@dataclass
class Loaded:
    """The members an export held, and each line that could not be read."""

    members: list[Member] = field(default_factory=list)
    bad_lines: list[tuple[int, str]] = field(default_factory=list)


def parse_member(line: str) -> Member:
    """The member on `line`, such as `Ann Lee,ann@example.org,2019`."""
    name, email, joined = line.strip().split(",")
    if "@" not in email:
        raise ValueError(f"not an email address: {email!r}")
    return Member(name.strip(), email.strip(), int(joined))


def load_members(lines: Iterable[str]) -> Loaded:
    """Every member in the export `lines`, and every line that is not one."""
    loaded = Loaded()
    for number, line in enumerate(lines, start=1):
        if not line.strip():
            continue
        try:
            loaded.members.append(parse_member(line))
        except ValueError as error:
            loaded.bad_lines.append((number, str(error)))
    return loaded
