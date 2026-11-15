"""Find the items running low and email the shop about them."""

import smtplib
from email.message import EmailMessage


def low_items(stock, cfg):
    """The names of the items whose count is under the low-stock threshold."""
    threshold = cfg["low_stock_threshold"]
    return [name for name, count in stock.items() if count < threshold]


def send_alert(items, cfg):
    msg = EmailMessage()
    msg["To"] = cfg["alert_to"]
    msg["From"] = "stocktake@shop.example.com"
    msg["Subject"] = f"Low stock: {', '.join(items)}"
    msg.set_content("\n".join(items))
    with smtplib.SMTP(cfg.get("smtp_host", "localhost")) as smtp:
        smtp.send_message(msg)
