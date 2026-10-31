"""The plantkit command."""

from plantkit.cli import main


def test_sow_prints_the_dates(capsys):
    assert main(["sow", "examples/garden.toml"]) == 0
    assert capsys.readouterr().out.splitlines()[0] == "2026-02-09 onion"


def test_sow_writes_a_file(tmp_path, capsys):
    out = tmp_path / "sow.txt"
    assert main(["sow", "examples/garden.toml", "--out", str(out)]) == 0
    assert capsys.readouterr().out == ""
    assert out.read_text().endswith("2026-04-06 bean\n")


def test_unknown_plant_exits_2(tmp_path, capsys):
    garden = tmp_path / "garden.toml"
    garden.write_text('name = "x"\nlast_frost = 2026-04-20\nfirst_frost = 2026-10-25\n[beds]\na = ["yam"]\n')
    assert main(["sow", str(garden)]) == 2
    assert capsys.readouterr().err.startswith("plantkit: ")
