"""Orders by month. Each order has id, customer, created_at, total, currency and
refunded_at (a timezone-aware datetime, or None)."""

ORDERS = []


def orders_in(month):
    return [o for o in ORDERS if o["created_at"].startswith(month)]
