from datetime import datetime

from greenhouse.log import append_reading
from greenhouse.sensor import parse_celsius


def test_parses_millidegrees():
    assert parse_celsius("4b 01 4b 46 7f ff 05 10 e1 : crc=e1 YES\n4b 01 t=3875\n") == 3.875


def test_header_written_once(tmp_path):
    log = tmp_path / "g.csv"
    append_reading(log, datetime(2026, 10, 1, 6, 0), 5.0)
    append_reading(log, datetime(2026, 10, 1, 6, 10), 4.5)
    assert log.read_text().splitlines() == ["time,celsius", "2026-10-01T06:00,5.0", "2026-10-01T06:10,4.5"]
