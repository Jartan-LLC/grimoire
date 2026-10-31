"""Users, kept in memory for now."""

from dataclasses import dataclass


@dataclass
class User:
    id: int
    name: str
    email: str
    active: bool = True


USERS: dict[int, User] = {1: User(1, "Ada", "ada@example.com"), 2: User(2, "Lin", "lin@example.com")}


def get_user(user_id: int) -> User | None:
    """The user with `user_id`, or None when there is none."""
    return USERS.get(user_id)
