from fileshare import files


def test_serves_an_upload(tmp_path, monkeypatch):
    (tmp_path / "a.txt").write_text("hi")
    monkeypatch.setattr(files, "UPLOADS", str(tmp_path))
    assert files.serve_file("a.txt") == b"hi"
