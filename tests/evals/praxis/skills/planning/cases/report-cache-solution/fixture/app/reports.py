from app import db


def get_report(customer_id, month):
    orders = db.orders_for(customer_id, month)
    lines = []
    for order in orders:
        items = db.fetch_items(order["id"])
        lines.append({"order": order["id"], "total": sum(i["price"] for i in items)})
    return {"customer": customer_id, "month": month, "lines": lines}
