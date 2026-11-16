"""Write a month's invoices as a CSV file for the finance team."""

import csv
from decimal import Decimal

HEADER = ["invoice", "customer", "amount"]


def format_row(invoice: dict[str, object]) -> list[str]:
    """One CSV row for `invoice`; the amount is in cents."""
    amount = invoice["amount"]
    if not isinstance(amount, Decimal):
        raise ValueError(f"invoice {invoice['id']}: amount {amount!r} is not a Decimal")
    return [str(invoice["id"]), str(invoice["customer"]), f"{amount:.2f}"]


def export_csv(path: str, invoices: list[dict[str, object]]) -> None:
    """Write `invoices` to the CSV file at `path`, replacing it."""
    out = open(path, "w", newline="")
    writer = csv.writer(out)
    writer.writerow(HEADER)
    for invoice in invoices:
        writer.writerow(format_row(invoice))
    out.close()
