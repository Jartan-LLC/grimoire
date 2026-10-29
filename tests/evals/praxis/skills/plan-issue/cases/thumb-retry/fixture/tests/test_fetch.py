import io
import urllib.error

import pytest

from feeds import fetch


def test_retries_a_503_then_succeeds(monkeypatch):
    answers = [urllib.error.HTTPError("u", 503, "busy", None, None), io.BytesIO(b"<rss/>")]

    def fake_urlopen(url, timeout):
        answer = answers.pop(0)
        if isinstance(answer, Exception):
            raise answer
        return answer

    monkeypatch.setattr(fetch.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(fetch.time, "sleep", lambda s: None)
    assert fetch.fetch_feed("http://feed") == b"<rss/>"


def test_does_not_retry_a_404(monkeypatch):
    calls = []

    def fake_urlopen(url, timeout):
        calls.append(url)
        raise urllib.error.HTTPError(url, 404, "gone", None, None)

    monkeypatch.setattr(fetch.urllib.request, "urlopen", fake_urlopen)
    with pytest.raises(urllib.error.HTTPError):
        fetch.fetch_feed("http://feed")
    assert len(calls) == 1
