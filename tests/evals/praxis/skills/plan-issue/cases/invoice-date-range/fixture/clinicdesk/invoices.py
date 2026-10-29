"""GET /invoices."""

from clinicdesk import db


def list_invoices(query: dict[str, str]) -> list[dict]:
    """Every invoice, oldest first."""
    return sorted(db.INVOICES, key=lambda i: i["day"])
