"""Invoices."""

from .users import get_user


def invoice_email(invoice: dict) -> str | None:
    user = get_user(invoice["user_id"])
    return user.email if user else None
