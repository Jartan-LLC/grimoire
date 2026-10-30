from confload import load_config, parse_window


def test_parse_window():
    assert parse_window("5m") == 300


def test_load_config(tmp_path):
    path = tmp_path / "app.toml"
    path.write_text('name = "demo"\nwindow = "30s"\n')
    assert load_config(path) == {"name": "demo", "window": 30}
