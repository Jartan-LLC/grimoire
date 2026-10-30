"""Notify."""

from .users import get_user


def greeting(user_id: int) -> str:
    user = get_user(user_id)
    return f"Hello {user.name}" if user else "Hello"
