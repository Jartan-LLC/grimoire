from billing.models import Subscription


def test_defaults():
    assert Subscription(1).active
