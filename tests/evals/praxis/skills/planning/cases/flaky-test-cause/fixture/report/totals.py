"""Monthly totals."""

_CACHE = {}


def month_total(orders, month):
    if month not in _CACHE:
        _CACHE[month] = sum(o["amount"] for o in orders if o["month"] == month)
    return _CACHE[month]
