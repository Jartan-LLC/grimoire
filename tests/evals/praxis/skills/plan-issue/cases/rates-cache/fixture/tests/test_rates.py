import io
import json
from decimal import Decimal
from unittest import mock

from fxconv import rates


def test_convert_rounds_half_even():
    assert rates.convert(Decimal("10.00"), Decimal("1.0825")) == Decimal("10.82")


def test_fetch_reads_rates_as_decimals():
    body = io.BytesIO(json.dumps({"rates": {"USD": 1.0825}}).encode())
    with mock.patch("urllib.request.urlopen", return_value=body):
        assert rates.fetch_rates("EUR") == {"USD": Decimal("1.0825")}
