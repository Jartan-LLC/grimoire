from habits.cli import main


def test_report_counts(tmp_path, monkeypatch, capsys):
    log = tmp_path / "habits.log"
    log.write_text("2026-10-01 run\n2026-10-02 run\n2026-10-02 read\n")
    monkeypatch.setenv("HABITS_LOG", str(log))
    main(["report"])
    assert capsys.readouterr().out.splitlines() == ["read         1", "run          2"]
