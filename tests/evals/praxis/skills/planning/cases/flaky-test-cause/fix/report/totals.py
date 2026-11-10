"""Monthly totals."""


def month_total(orders, month):
    return sum(o["amount"] for o in orders if o["month"] == month)
