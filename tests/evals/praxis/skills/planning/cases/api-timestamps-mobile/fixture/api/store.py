"""Orders, kept in memory in this example."""

ORDERS = {}


def get(order_id):
    return ORDERS[order_id]
