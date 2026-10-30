from crm.orders import order_owner


def test_owner():
    assert order_owner({"user_id": 2}) == "Lin"
    assert order_owner({"user_id": 9}) == "unknown"
