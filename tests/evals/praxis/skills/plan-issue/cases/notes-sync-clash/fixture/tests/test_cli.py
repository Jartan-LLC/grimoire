from notes.cli import main


def test_add_then_list(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path))
    main(["add", "Standup", "Moved the release"])
    main(["list"])
    assert capsys.readouterr().out.splitlines()[-1] == "   1  Standup"


def test_sync_copies_notes(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("NOTES_DIR", str(tmp_path / "notes"))
    monkeypatch.setenv("NOTES_BACKUP_DIR", str(tmp_path / "backup"))
    main(["add", "A", "a"])
    main(["sync"])
    assert (tmp_path / "backup" / "1.md").is_file()
    assert capsys.readouterr().out.splitlines()[-1] == "copied 1 notes"
