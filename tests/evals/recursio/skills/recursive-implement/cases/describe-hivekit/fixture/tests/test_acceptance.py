"""Acceptance tests for hivekit, as the README specifies."""

from datetime import date

import pytest

from hivekit.cli import main
from hivekit.health import flags, overdue
from hivekit.honey import FRAME_KG, gains, honey_kg
from hivekit.log import Inspection, LogError, by_hive, parse_log

LOG = """hive,date,brood,honey,queen,temper
oak,2026-06-20,6,2,no,2
elm,2026-06-14,5,3,yes,4
oak,2026-06-06,7,1,yes,1

oak,2026-06-13,5,5,no,1
elm,2026-06-01,4,2,yes,2
ash,2026-06-17,5,3,yes,3
"""


def log():
    return parse_log(LOG)


def test_log_sorted_by_hive_then_date():
    """Rows come back sorted by hive, then date."""
    rows = log()
    assert [(r.hive, r.date.day) for r in rows] == [("ash", 17), ("elm", 1), ("elm", 14), ("oak", 6), ("oak", 13), ("oak", 20)]
    assert rows[0] == Inspection("ash", date(2026, 6, 17), 5, 3, True, 3)


@pytest.mark.parametrize("row", ["oak,2026-06-27,11,0,yes,1", "oak,2026-06-27,5,0,maybe,1", "oak,27 June,5,0,yes,1", "oak,2026-06-27,5,0,yes"])
def test_bad_row_names_its_line(row):
    """A bad row raises LogError naming its line."""
    with pytest.raises(LogError, match=r"^line 3: "):
        parse_log(f"hive,date,brood,honey,queen,temper\nelm,2026-06-01,4,2,yes,2\n{row}\n")


def test_two_rows_on_one_date_name_the_hive():
    """A hive inspected twice on one date is an error naming the hive."""
    with pytest.raises(LogError, match="elm"):
        parse_log("hive,date,brood,honey,queen,temper\nelm,2026-06-01,4,2,yes,2\nelm,2026-06-01,4,3,yes,2\n")


def test_flags_on_the_latest_inspection():
    """Flags read the latest inspection, in their fixed order."""
    hives = by_hive(log())
    assert list(hives) == ["ash", "elm", "oak"]
    assert flags(hives["oak"]) == ["queenless"]
    assert flags(hives["elm"]) == ["defensive"]
    assert flags(hives["ash"]) == []
    crowded = [Inspection("fir", date(2026, 6, 1), 6, 3, False, 5)]
    assert flags(crowded) == ["crowded", "defensive"]


def test_overdue():
    """A hive is overdue once its latest inspection is more than ten days old."""
    assert overdue(log(), date(2026, 6, 28)) == ["ash", "elm"]
    assert overdue(log(), date(2026, 6, 28), days=5) == ["ash", "elm", "oak"]


def test_honey():
    """Honey is frames times FRAME_KG; gains are the change from one inspection to the next."""
    oak = by_hive(log())["oak"]
    assert honey_kg(oak[1]) == pytest.approx(5 * FRAME_KG)
    (first, up), (second, down) = gains(oak)
    assert (first, second) == (date(2026, 6, 13), date(2026, 6, 20))
    assert (up, down) == (pytest.approx(4 * FRAME_KG), pytest.approx(-3 * FRAME_KG))


@pytest.fixture
def log_file(tmp_path):
    path = tmp_path / "log.csv"
    path.write_text(LOG)
    return str(path)


def test_cli_status(log_file, capsys):
    """Status prints each hive's latest date, its flags or ok, and whether it is overdue."""
    assert main(["status", log_file, "--today", "2026-06-28"]) == 0
    assert capsys.readouterr().out == (
        "ash 2026-06-17 ok (overdue)\nelm 2026-06-14 defensive (overdue)\noak 2026-06-20 queenless\n"
    )


def test_cli_honey(log_file, capsys):
    """Honey prints each hive's latest honey in kilograms."""
    assert main(["honey", log_file]) == 0
    assert capsys.readouterr().out == f"ash {3 * FRAME_KG:.1f}\nelm {3 * FRAME_KG:.1f}\noak {2 * FRAME_KG:.1f}\n"


def test_cli_bad_log_exits_2(tmp_path, capsys):
    """A bad log exits 2 with the line in the message."""
    path = tmp_path / "log.csv"
    path.write_text("hive,date,brood,honey,queen,temper\noak,2026-06-01,4,2,yes,9\n")
    assert main(["honey", str(path)]) == 2
    assert capsys.readouterr().err.startswith("hivekit: line 2: ")
