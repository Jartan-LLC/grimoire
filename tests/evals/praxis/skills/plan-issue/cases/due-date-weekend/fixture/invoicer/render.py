"""Render an invoice as plain text."""

from datetime import date

from invoicer.dates import due_date


def render(order: dict, issued: date) -> str:
    """The invoice text for `order`, issued on `issued`."""
    lines = [f"Invoice {order['number']}", f"Issued: {issued.isoformat()}"]
    total = 0
    for item in order["items"]:
        amount = item["qty"] * item["unit_cents"]
        total += amount
        lines.append(f"  {item['name']:<30} {amount / 100:>10.2f}")
    lines.append(f"  {'Total':<30} {total / 100:>10.2f}")
    due = due_date(issued, order.get("terms_days", 14))
    lines.append(f"Due: {due.strftime('%A %d %B %Y')}")
    return "\n".join(lines)
