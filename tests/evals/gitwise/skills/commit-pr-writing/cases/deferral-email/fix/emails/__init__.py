"""Email address checks."""

import re

_EMAIL = re.compile(r"^[a-z0-9.+]+@[a-z0-9-]+(\.[a-z0-9-]+)+$")


def is_valid_email(address: str) -> bool:
    """Whether `address` looks like an email address."""
    return bool(_EMAIL.match(address.lower()))
