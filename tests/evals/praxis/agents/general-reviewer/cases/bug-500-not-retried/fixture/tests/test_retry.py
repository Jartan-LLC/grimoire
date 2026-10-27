from fetchkit.retry import with_retries
from fetchkit.transport import Response


def test_a_success_is_returned_at_once() -> None:
    calls = []

    def call() -> Response:
        calls.append(1)
        return Response(200, "ok")

    assert with_retries(call, sleep=lambda s: None).ok
    assert len(calls) == 1
