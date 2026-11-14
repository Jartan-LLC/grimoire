"""Admin tasks: python3 tools/admin_cli.py export-orders > orders.csv"""
import csv
import sys

import requests

BASE = "http://orders.internal:8000"


def export_orders():
    orders = requests.get(f"{BASE}/internal/orders", timeout=60).json()
    out = csv.DictWriter(sys.stdout, fieldnames=["id", "customer", "total", "created_at"])
    out.writeheader()
    out.writerows(orders)


if __name__ == "__main__":
    {"export-orders": export_orders}[sys.argv[1]]()
