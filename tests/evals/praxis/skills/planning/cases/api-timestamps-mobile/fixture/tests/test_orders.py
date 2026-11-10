from datetime import UTC, datetime

from api.orders import serialize


def test_created_at_is_milliseconds():
    order = {"id": 1, "total": 500, "created_at": datetime(2026, 1, 1, tzinfo=UTC)}
    assert serialize(order)["created_at"] == 1767225600000
