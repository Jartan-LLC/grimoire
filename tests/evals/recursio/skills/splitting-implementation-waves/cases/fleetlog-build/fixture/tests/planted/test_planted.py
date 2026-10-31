"""Planted acceptance tests: one basic check per module and two for the command."""

import contextlib
import datetime as dt
import io
import pathlib
import sys
import tempfile
import unittest
from decimal import Decimal as D

# conftest.py puts src/ on the path for pytest; unittest does not read it.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "src"))

from fleetlog import FillUp, FuelKind, ServiceRecord, Trip, Vehicle
from fleetlog import cli, costs, economy, service, trips

FILLS = [
    FillUp("AB12", dt.date(2026, 3, 20), 11100, D("30"), D("54.00")),
    FillUp("AB12", dt.date(2026, 3, 1), 10000, D("40"), D("70.00")),
    FillUp("AB12", dt.date(2026, 3, 6), 10300, D("10"), D("18.00"), full=False),
    FillUp("AB12", dt.date(2026, 3, 12), 10600, D("26"), D("46.80")),
]

CAR = Vehicle("AB12", "Skoda", FuelKind.PETROL, dt.date(2025, 1, 1), D("20000"))

TRIPS = [
    Trip("AB12", "ann", dt.datetime(2026, 3, 2, 8), dt.datetime(2026, 3, 2, 9), 0, 50),
    Trip("AB12", "ann", dt.datetime(2026, 3, 2, 10), dt.datetime(2026, 3, 2, 11), 60, 100),
    Trip("CD34", "ann", dt.datetime(2026, 3, 2, 10, 30), dt.datetime(2026, 3, 2, 11, 30), 500, 540),
]


def run(argv):
    """The exit code of `cli.main(argv)` and what it printed."""
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = cli.main(argv)
    return code, out.getvalue()


class PlantedTest(unittest.TestCase):
    def test_economy_segments_and_average(self):
        segs = economy.segments(FILLS)
        assert [(s.start_km, s.end_km, s.litres, s.l_per_100km) for s in segs] == [
            (10000, 10600, D("36"), D("6.00")),
            (10600, 11100, D("30"), D("6.00")),
        ]
        assert economy.average(FILLS) == D("6.00")

    def test_service_due_statuses_and_order(self):
        records = [ServiceRecord("AB12", dt.date(2025, 6, 1), 10000, "oil", D("120"))]
        got = service.due(CAR, records, dt.date(2026, 5, 15), 24500)
        assert [(d.kind, d.status) for d in got] == [
            ("tyres", "overdue"), ("oil", "due-soon"), ("brakes", "ok"), ("inspection", "ok"),
        ]
        oil = next(d for d in got if d.kind == "oil")
        assert (oil.due_day, oil.due_km) == (dt.date(2026, 6, 1), 25000)
        ev = Vehicle("EV01", "Kia", FuelKind.ELECTRIC, dt.date(2025, 1, 1), D("30000"))
        assert "oil" not in {d.kind for d in service.due(ev, [], dt.date(2025, 2, 1), 100)}

    def test_trip_check_and_mileage(self):
        got = trips.check(TRIPS)
        assert [(p.trip, p.kind) for p in got] == [(1, "gap"), (2, "driver")]
        assert got[0].detail == "gap of 10 km"
        assert trips.mileage(TRIPS, 2026, 3) == {"ann": 130}

    def test_running_costs(self):
        car = Vehicle("AB12", "Skoda", FuelKind.PETROL, dt.date(2024, 1, 1), D("20000"))
        fills = [
            FillUp("AB12", dt.date(2024, 12, 31), 9500, D("30"), D("50.00")),
            FillUp("AB12", dt.date(2025, 3, 1), 10000, D("40"), D("70.00")),
            FillUp("AB12", dt.date(2025, 6, 1), 10600, D("35"), D("60.00")),
            FillUp("ZZ99", dt.date(2025, 6, 1), 400, D("35"), D("60.00")),
        ]
        services = [ServiceRecord("AB12", dt.date(2025, 9, 1), 11000, "oil", D("150.00"))]
        c = costs.running_costs(car, fills, services, dt.date(2025, 1, 1), dt.date(2025, 12, 31))
        assert (c.fuel, c.service, c.depreciation) == (D("130.00"), D("150.00"), D("2242.30"))
        assert (c.total, c.distance_km, c.per_km) == (D("2522.30"), 1000, D("2.522"))

    def test_cli_check_and_economy(self):
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = pathlib.Path(tmp)
            t = tmp_path / "trips.csv"
            t.write_text(
                "reg,driver,start,end,start_km,end_km,purpose\n"
                "AB12,ann,2026-03-02T08:00,2026-03-02T09:00,0,50,site\n"
                "AB12,ann,2026-03-02T10:00,2026-03-02T11:00,60,100,site\n"
            )
            code, out = run(["check", str(t)])
            assert code == 1
            assert "trip 2: gap: gap of 10 km" in out
            f = tmp_path / "fills.csv"
            f.write_text(
                "reg,day,odometer_km,litres,cost,full\n"
                "AB12,2026-03-01,10000,40,70.00,yes\n"
                "AB12,2026-03-06,10300,10,18.00,no\n"
                "AB12,2026-03-12,10600,26,46.80,yes\n"
            )
            code, out = run(["economy", str(f), "--reg", "AB12"])
            assert code == 0
            assert out.splitlines() == ["10000-10600 6.00", "average 6.00"]
