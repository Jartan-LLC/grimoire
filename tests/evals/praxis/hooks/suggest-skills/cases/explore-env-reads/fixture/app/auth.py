"""Signing session cookies."""

import hashlib
import hmac
import os


def sign(value: str) -> str:
    """`value` with its signature."""
    key = os.environ["NOTES_SECRET_KEY"].encode()
    return value + "." + hmac.new(key, value.encode(), hashlib.sha256).hexdigest()
