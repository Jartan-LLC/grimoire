import pytest

from shop.orders import Order


def test_new_order_has_nothing_refunded():
    assert Order(1000).refunded_cents == 0


def test_full_refund():
    order = Order(1000)
    order.refund(1000)
    assert order.refunded_cents == 1000


def test_partial_refunds_add_up():
    order = Order(1000)
    order.refund(300)
    order.refund(200)
    assert order.refunded_cents == 500


def test_over_refund_is_refused():
    with pytest.raises(ValueError):
        Order(1000).refund(1001)


def test_notes_start_empty():
    assert Order(5).notes == []
