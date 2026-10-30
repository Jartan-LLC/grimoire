"""Reports."""

from .users import get_user


def active_names(ids: list[int]) -> list[str]:
    users = [get_user(i) for i in ids]
    return [u.name for u in users if u and u.active]
