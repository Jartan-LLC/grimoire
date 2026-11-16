from notifier.templates import order_confirmation, shipped


def test_confirmation_names_the_order():
    subject, body = order_confirmation("A17", "12.50 EUR")
    assert subject == "Order A17 confirmed"
    assert "12.50 EUR" in body


def test_shipped_gives_the_tracking_number():
    _, body = shipped("A17", "TRK-9")
    assert "TRK-9" in body
