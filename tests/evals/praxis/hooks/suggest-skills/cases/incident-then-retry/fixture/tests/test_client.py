import pytest

from stockroom.client import PriceUnavailable, fetch_price
from stockroom.transport import Response


class FakeTransport:
    def __init__(self, *answers):
        self.answers = list(answers)
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        answer = self.answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer


def test_returns_the_price():
    transport = FakeTransport(Response(200, {"price": 4.5}))
    assert fetch_price("A-1", transport) == 4.5
    assert transport.urls == ["https://pricing.internal/v1/price/A-1"]


def test_an_unknown_sku_is_unavailable():
    with pytest.raises(PriceUnavailable):
        fetch_price("A-1", FakeTransport(Response(404, {})))
