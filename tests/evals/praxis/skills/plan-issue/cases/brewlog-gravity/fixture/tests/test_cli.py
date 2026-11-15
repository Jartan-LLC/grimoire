from brewlog.cli import main


def test_list_prints_each_brew(tmp_path, monkeypatch, capsys):
    log = tmp_path / "brews.csv"
    log.write_text("2026-10-01,Pale Ale,pale\n2026-10-15,Oat Stout,stout\n")
    monkeypatch.setenv("BREWLOG_FILE", str(log))
    main(["list"])
    assert capsys.readouterr().out.splitlines() == [
        "2026-10-01  Pale Ale (pale)",
        "2026-10-15  Oat Stout (stout)",
    ]
