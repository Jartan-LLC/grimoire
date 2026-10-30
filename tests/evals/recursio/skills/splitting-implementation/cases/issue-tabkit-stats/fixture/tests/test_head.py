from tabkit.cli import main


def test_head_prints_the_header_and_rows(tmp_path, capsys):
    path = tmp_path / "t.csv"
    path.write_text("a,b\n1,2\n3,4\n")
    assert main(["head", str(path), "-n", "1"]) == 0
    assert capsys.readouterr().out == "a,b\n1,2\n"
