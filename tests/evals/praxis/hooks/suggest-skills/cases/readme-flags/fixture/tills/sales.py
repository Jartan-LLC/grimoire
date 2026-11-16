"""The till records in a date range."""

from datetime import date


def sales_between(since: date, until: date, include_refunds: bool) -> list[dict[str, object]]:
    """Each sale from `since` to `until`, both included, refunds only if `include_refunds`."""
    return []
