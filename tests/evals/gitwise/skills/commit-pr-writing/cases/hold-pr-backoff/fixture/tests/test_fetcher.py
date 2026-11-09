from fetcher import RETRIES


def test_retries() -> None:
    assert RETRIES == 3
