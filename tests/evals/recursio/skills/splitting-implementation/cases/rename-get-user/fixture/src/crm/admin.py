"""Admin."""

from .users import get_user


def deactivate(user_id: int) -> bool:
    user = get_user(user_id)
    if user is None:
        return False
    user.active = False
    return True
