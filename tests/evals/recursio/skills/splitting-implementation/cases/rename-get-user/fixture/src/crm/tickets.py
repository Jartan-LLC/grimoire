"""Tickets."""

from .users import get_user


def ticket_is_from_active_user(ticket: dict) -> bool:
    user = get_user(ticket["user_id"])
    return bool(user and user.active)
