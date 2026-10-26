import io

from rates import fetch_rates


def test_reads_json() -> None:
    def opener(url, **kwargs):
        return io.BytesIO(b'{"EUR": 0.9}')

    assert fetch_rates(opener) == {"EUR": 0.9}
