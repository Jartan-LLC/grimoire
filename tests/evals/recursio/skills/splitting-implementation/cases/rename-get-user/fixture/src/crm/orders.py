"""Orders."""

from .users import get_user


def order_owner(order: dict) -> str:
    user = get_user(order["user_id"])
    return user.name if user else "unknown"
