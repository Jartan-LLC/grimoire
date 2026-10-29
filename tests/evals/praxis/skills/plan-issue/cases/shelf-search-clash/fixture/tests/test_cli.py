from shelf.cli import main


def test_add_then_search(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SHELF_FILE", str(tmp_path / "shelf.json"))
    main(["add", "Dune", "Frank Herbert", "--room", "study"])
    main(["add", "Emma", "Jane Austen"])
    capsys.readouterr()
    main(["search", "herbert"])
    assert capsys.readouterr().out == "   1  Dune -- Frank Herbert  [study]\n"


def test_remove(tmp_path, monkeypatch, capsys):
    monkeypatch.setenv("SHELF_FILE", str(tmp_path / "shelf.json"))
    main(["add", "Dune", "Frank Herbert"])
    main(["remove", "1"])
    capsys.readouterr()
    main(["list"])
    assert capsys.readouterr().out == ""
