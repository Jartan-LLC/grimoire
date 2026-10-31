"""Acceptance tests for the next release, as the README specifies."""

from datetime import date

import pytest

from plantkit.cli import main
from plantkit.companions import conflicts
from plantkit.model import GardenError, load_garden
from plantkit.rain import parse_rain
from plantkit.watering import weekly_water

GARDEN = "examples/garden.toml"
RAIN = "date,mm\n2026-05-31,7\n2026-06-01,4.5\n\n2026-06-03,10\n2026-06-07,3\n2026-06-08,20\n"


def test_parse_rain_adds_up_a_repeated_date():
    assert parse_rain("date,mm\n2026-06-01,1.5\n2026-06-01,2\n") == {date(2026, 6, 1): 3.5}


@pytest.mark.parametrize("row", ["2026-06-01,-1", "2026-06-01", "June 1,3", "2026-06-01,lots"])
def test_bad_rain_names_its_line(row):
    with pytest.raises(GardenError, match=r"^line 3: "):
        parse_rain(f"date,mm\n2026-05-31,2\n{row}\n")


def test_weekly_water_takes_off_the_week_s_rain():
    rain = parse_rain(RAIN)
    assert weekly_water(load_garden(GARDEN), rain, date(2026, 6, 1)) == {"north": 37.5, "south": 25.5}
    assert weekly_water(load_garden(GARDEN), {date(2026, 6, 2): 80.0}, date(2026, 6, 1)) == {"north": 0, "south": 0}


def test_weekly_water_needs_a_monday():
    with pytest.raises(GardenError):
        weekly_water(load_garden(GARDEN), {}, date(2026, 6, 2))


def test_conflicts():
    assert conflicts(load_garden(GARDEN)) == [("south", "bean", "onion")]


def test_cli_water(tmp_path, capsys):
    rain = tmp_path / "rain.csv"
    rain.write_text(RAIN)
    assert main(["water", GARDEN, str(rain), "--week", "2026-06-01"]) == 0
    assert capsys.readouterr().out == "north 37.5\nsouth 25.5\n"


def test_cli_water_to_a_file(tmp_path, capsys):
    rain = tmp_path / "rain.csv"
    rain.write_text(RAIN)
    out = tmp_path / "water.txt"
    assert main(["water", GARDEN, str(rain), "--week", "2026-06-01", "--output", str(out)]) == 0
    assert capsys.readouterr().out == ""
    assert out.read_text() == "north 37.5\nsouth 25.5\n"


def test_cli_check(tmp_path, capsys):
    assert main(["check", GARDEN]) == 1
    assert capsys.readouterr().out == "south: bean + onion\n"
    calm = tmp_path / "calm.toml"
    calm.write_text('name = "calm"\nlast_frost = 2026-04-20\nfirst_frost = 2026-10-25\n[beds]\na = ["kale", "onion"]\n')
    assert main(["check", str(calm)]) == 0
    assert capsys.readouterr().out == ""


def test_cli_bad_rain_exits_2(tmp_path, capsys):
    rain = tmp_path / "rain.csv"
    rain.write_text("date,mm\n2026-06-01,-4\n")
    assert main(["water", GARDEN, str(rain), "--week", "2026-06-01"]) == 2
    assert capsys.readouterr().err.startswith("plantkit: line 2: ")
