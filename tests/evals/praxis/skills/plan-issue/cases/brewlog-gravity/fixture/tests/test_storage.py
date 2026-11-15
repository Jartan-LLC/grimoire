from brewlog import storage


def test_append_then_load(tmp_path):
    file = str(tmp_path / "brews.csv")
    storage.append(file, {"date": "2026-10-01", "name": "Pale Ale", "style": "pale"})
    assert storage.load(file) == [{"date": "2026-10-01", "name": "Pale Ale", "style": "pale"}]


def test_missing_file_is_empty(tmp_path):
    assert storage.load(str(tmp_path / "none.csv")) == []
