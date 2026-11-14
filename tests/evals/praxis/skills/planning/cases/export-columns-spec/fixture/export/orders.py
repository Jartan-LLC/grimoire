"""The monthly orders CSV."""

import csv

from export import db

COLUMNS = ["id", "customer", "created_at", "total"]


def rows(month):
    for order in db.orders_in(month):
        yield [order["id"], order["customer"], order["created_at"], order["total"]]


def write_month(month):
    with open(f"orders-{month}.csv", "w", newline="") as f:
        out = csv.writer(f)
        out.writerow(COLUMNS)
        out.writerows(rows(month))
