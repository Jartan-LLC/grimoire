import io
import urllib.error

from feeds import thumbs


def test_downloads_once_then_uses_the_cache(tmp_path, monkeypatch):
    calls = []

    def fake_urlopen(url, timeout):
        calls.append(url)
        return io.BytesIO(b"png")

    monkeypatch.setattr(thumbs.urllib.request, "urlopen", fake_urlopen)
    first = thumbs.download_thumb("http://img/1", tmp_path)
    second = thumbs.download_thumb("http://img/1", tmp_path)
    assert first == second
    assert first.read_bytes() == b"png"
    assert len(calls) == 1


def test_failed_download_gives_none(tmp_path, monkeypatch):
    def fake_urlopen(url, timeout):
        raise urllib.error.URLError("down")

    monkeypatch.setattr(thumbs.urllib.request, "urlopen", fake_urlopen)
    assert thumbs.download_thumb("http://img/2", tmp_path) is None
