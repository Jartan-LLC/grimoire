from confkit.cli import main


def test_check_accepts_valid_toml(tmp_path, capsys):
    path = tmp_path / "c.toml"
    path.write_text('name = "x"\n')
    assert main(["check", str(path)]) == 0
    assert capsys.readouterr().out.endswith(": ok\n")
