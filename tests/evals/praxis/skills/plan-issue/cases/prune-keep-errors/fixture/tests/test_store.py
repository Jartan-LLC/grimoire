from backupctl import store


def test_prune_keeps_seven(tmp_path, monkeypatch):
    monkeypatch.setattr(store, "ROOT", tmp_path)
    for day in range(1, 11):
        (tmp_path / f"2026-11-{day:02}.dump").write_text("x")
    store.prune()
    assert len(list(tmp_path.glob("*.dump"))) == 7
