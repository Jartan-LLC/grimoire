from pantry.cli import main


def test_show_prints_ingredients(monkeypatch, capsys):
    monkeypatch.setenv("PANTRY_DIR", "recipes")
    main(["show", "pancakes"])
    out = capsys.readouterr().out.splitlines()
    assert out[:2] == ["Pancakes", "Serves 4"]
    assert "  1.5 cup flour" in out
