from ledgerpush import upload


def test_upload_sends_the_file(tmp_path, monkeypatch):
    sent = []

    class Conn:
        def __enter__(self):
            return self

        def __exit__(self, *exc):
            return False

        def sendall(self, data):
            sent.append(data)

    monkeypatch.setattr("socket.create_connection", lambda *a, **k: Conn())
    f = tmp_path / "export.csv"
    f.write_text("a,b\n")
    upload.upload(f)
    assert sent == [b"a,b\n"]
