# SPDX-License-Identifier: MIT
"""Acceptance tests for meterkit, as the README specifies."""

from datetime import datetime
from decimal import Decimal

import pytest

from meterkit.anomaly import anomalies
from meterkit.cli import main
from meterkit.readings import Interval, Reading, ReadingError, intervals, parse_readings
from meterkit.tariff import Tariff, bill

CSV = """meter,time,register
m1,2026-03-01T06:00,100.000
m1,2026-03-01T08:00,101.500
m2,2026-03-01T06:00,99999.500

m1,2026-03-01T23:00,104.000
m2,2026-03-01T09:00,0.700
"""

TARIFF = Tariff(Decimal("0.30"), Decimal("0.10"), Decimal("0.50"))


def at(day: int, hour: int) -> datetime:
    return datetime(2026, 3, day, hour, 0)


def test_parse_readings_keeps_file_order():
    readings = parse_readings(CSV)
    assert len(readings) == 5
    assert readings[0] == Reading("m1", at(1, 6), Decimal("100.000"))
    assert readings[2] == Reading("m2", at(1, 6), Decimal("99999.500"))


def test_parse_error_names_the_line():
    with pytest.raises(ReadingError, match=r"^line 3: "):
        parse_readings("meter,time,register\nm1,2026-03-01T06:00,1\nm1,yesterday,2\n")


def test_intervals_handle_rollover_and_sort_by_meter():
    result = intervals(parse_readings(CSV))
    assert [(i.meter, i.start, i.end, i.kwh) for i in result] == [
        ("m1", at(1, 6), at(1, 8), Decimal("1.500")),
        ("m1", at(1, 8), at(1, 23), Decimal("2.500")),
        ("m2", at(1, 6), at(1, 9), Decimal("1.200")),
    ]


def test_two_readings_at_one_time_name_the_meter():
    text = "meter,time,register\nm7,2026-03-01T06:00,1\nm7,2026-03-01T06:00,2\n"
    with pytest.raises(ReadingError, match="m7"):
        intervals(parse_readings(text))


def test_bill_from_readings():
    result = bill(intervals(parse_readings(CSV)), TARIFF)
    assert result.peak_kwh == Decimal("2.5")
    assert result.offpeak_kwh == Decimal("2.7")
    assert result.days == 1
    assert result.total == Decimal("1.52")


def test_bill_rates_by_start_hour_and_counts_days():
    spans = [
        Interval("m1", at(1, 22), at(2, 1), Decimal("1")),
        Interval("m1", at(2, 1), at(2, 7), Decimal("2")),
        Interval("m1", at(2, 7), at(2, 9), Decimal("1")),
    ]
    result = bill(spans, TARIFF)
    assert (result.peak_kwh, result.offpeak_kwh, result.days) == (Decimal(2), Decimal(2), 2)
    assert result.total == Decimal("1.80")


def test_anomalies_against_each_meters_median():
    m1 = [Interval("m1", at(1, h), at(1, h + 1), Decimal(k)) for h, k in ((1, 1), (2, 1), (3, 1), (4, 10))]
    m2 = [Interval("m2", at(1, h), at(1, h + 1), Decimal(k)) for h, k in ((1, 1), (2, 50))]
    found = anomalies(m1 + m2)
    assert [(a.interval, a.median) for a in found] == [(m1[3], Decimal(1))]


def test_cli_usage(tmp_path, capsys):
    path = tmp_path / "readings.csv"
    path.write_text(CSV)
    assert main(["usage", str(path)]) == 0
    assert capsys.readouterr().out.splitlines() == [
        "m1 2026-03-01T06:00 2026-03-01T08:00 1.500",
        "m1 2026-03-01T08:00 2026-03-01T23:00 2.500",
        "m2 2026-03-01T06:00 2026-03-01T09:00 1.200",
    ]


def test_cli_bill_for_one_meter(tmp_path, capsys):
    path = tmp_path / "readings.csv"
    path.write_text(CSV)
    argv = ["bill", str(path), "--peak", "0.30", "--offpeak", "0.10", "--standing", "0.50", "--meter", "m2"]
    assert main(argv) == 0
    assert capsys.readouterr().out == "peak_kwh: 0.000\noffpeak_kwh: 1.200\ndays: 1\ntotal: 0.62\n"


def test_cli_anomalies_prints_nothing_when_none(tmp_path, capsys):
    path = tmp_path / "readings.csv"
    path.write_text(CSV)
    assert main(["anomalies", str(path)]) == 0
    assert capsys.readouterr().out == ""


def test_cli_bad_input_exits_2(tmp_path, capsys):
    path = tmp_path / "readings.csv"
    path.write_text("meter,time,register\nm1,2026-03-01T06:00,1\nm1,2026-03-01T07:00,-4\n")
    assert main(["usage", str(path)]) == 2
    assert capsys.readouterr().err.startswith("meterkit: line 3: ")
