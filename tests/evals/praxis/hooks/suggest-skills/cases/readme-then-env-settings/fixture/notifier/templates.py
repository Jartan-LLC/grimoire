"""The text of each email the shop sends."""


def order_confirmation(order_id: str, total: str) -> tuple[str, str]:
    """The subject and body confirming order `order_id`."""
    return f"Order {order_id} confirmed", f"Thanks for your order. Total: {total}."


def shipped(order_id: str, tracking: str) -> tuple[str, str]:
    """The subject and body saying order `order_id` has shipped."""
    return f"Order {order_id} shipped", f"Your order is on its way. Tracking: {tracking}."
