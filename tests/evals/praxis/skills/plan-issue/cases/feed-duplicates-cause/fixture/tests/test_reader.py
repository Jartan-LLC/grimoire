from feedlet import reader


def test_newest_sorts(monkeypatch):
    monkeypatch.setattr(reader, "posts", lambda url: [{"title": url, "guid": url, "date": url}])
    assert [p["title"] for p in reader.newest(["a", "b"])] == ["b", "a"]
