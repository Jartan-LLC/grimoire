from retry import retry


def test_returns() -> None:
    assert retry(lambda: 5) == 5


def test_retries_then_succeeds() -> None:
    calls = []

    def flaky() -> int:
        calls.append(1)
        if len(calls) < 3:
            raise ValueError("not yet")
        return 7

    assert retry(flaky, sleep=lambda _: None) == 7
    assert len(calls) == 3
