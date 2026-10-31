"""The `fleet` command: reads the CSV files and prints what the modules compute."""

import argparse
import csv
import datetime
import decimal
import sys
from decimal import Decimal

from . import costs, economy, service, trips
from .model import FillUp, FleetError, FuelKind, ServiceRecord, Trip, Vehicle


def _rows(path, columns):
    """Yield each row of the CSV at `path` as a dict, requiring the `columns` header."""
    try:
        with open(path, newline="") as f:
            reader = csv.DictReader(f)
            missing = [c for c in columns if c not in (reader.fieldnames or [])]
            if missing:
                raise FleetError(f"{path}: missing column(s) {', '.join(missing)}")
            yield from reader
    except OSError as e:
        raise FleetError(f"cannot read {path}: {e.strerror}") from e


def _parse(path, columns, build):
    records = []
    for number, row in enumerate(_rows(path, columns), start=2):
        try:
            records.append(build(row))
        except (ValueError, decimal.InvalidOperation) as e:
            raise FleetError(f"{path} line {number}: {e}") from e
    return records


def _day(text):
    return datetime.date.fromisoformat(text)


def _flag(text):
    if text not in ("yes", "no"):
        raise ValueError(f"full must be yes or no, not {text!r}")
    return text == "yes"


def read_vehicles(path):
    return _parse(
        path,
        ["reg", "make", "fuel", "bought", "price"],
        lambda r: Vehicle(r["reg"], r["make"], FuelKind(r["fuel"]), _day(r["bought"]), Decimal(r["price"])),
    )


def read_fillups(path):
    return _parse(
        path,
        ["reg", "day", "odometer_km", "litres", "cost", "full"],
        lambda r: FillUp(
            r["reg"], _day(r["day"]), int(r["odometer_km"]), Decimal(r["litres"]),
            Decimal(r["cost"]), _flag(r["full"]),
        ),
    )


def read_services(path):
    return _parse(
        path,
        ["reg", "day", "odometer_km", "kind", "cost"],
        lambda r: ServiceRecord(r["reg"], _day(r["day"]), int(r["odometer_km"]), r["kind"], Decimal(r["cost"])),
    )


def read_trips(path):
    return _parse(
        path,
        ["reg", "driver", "start", "end", "start_km", "end_km", "purpose"],
        lambda r: Trip(
            r["reg"], r["driver"], datetime.datetime.fromisoformat(r["start"]),
            datetime.datetime.fromisoformat(r["end"]), int(r["start_km"]), int(r["end_km"]), r["purpose"],
        ),
    )


def _vehicle(vehicles, reg):
    for v in vehicles:
        if v.reg == reg:
            return v
    raise FleetError(f"vehicle {reg} is not in the vehicles file")


def _economy(args):
    fillups = [f for f in read_fillups(args.fillups) if f.reg == args.reg]
    for s in economy.segments(fillups):
        print(f"{s.start_km}-{s.end_km} {s.l_per_100km}")
    print(f"average {economy.average(fillups)}")
    return 0


def _due(args):
    vehicle = _vehicle(read_vehicles(args.vehicles), args.reg)
    records = [r for r in read_services(args.services) if r.reg == args.reg]
    items = service.due(vehicle, records, args.today, args.odometer)
    for d in items:
        parts = [str(p) for p in (d.due_day, d.due_km) if p is not None]
        print(f"{d.kind} {d.status} {' or '.join(parts)}")
    return 1 if any(d.status == "overdue" for d in items) else 0


def _check(args):
    problems = trips.check(read_trips(args.trips))
    for p in problems:
        print(f"trip {p.trip + 1}: {p.kind}: {p.detail}")
    return 1 if problems else 0


def _costs(args):
    vehicle = _vehicle(read_vehicles(args.vehicles), args.reg)
    result = costs.running_costs(
        vehicle, read_fillups(args.fillups), read_services(args.services), args.start, args.end
    )
    for name in ("fuel", "service", "depreciation", "total", "distance_km", "per_km"):
        print(f"{name} {getattr(result, name)}")
    return 0


def _date_arg(text):
    try:
        return _day(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not an ISO date: {text!r}") from None


def _parser():
    parser = argparse.ArgumentParser(prog="fleet", description="Answer questions about the fleet's records.")
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("economy", help="fuel economy of one vehicle")
    p.add_argument("fillups")
    p.add_argument("--reg", required=True)
    p.set_defaults(run=_economy)

    p = sub.add_parser("due", help="service items due for one vehicle")
    p.add_argument("vehicles")
    p.add_argument("services")
    p.add_argument("--reg", required=True)
    p.add_argument("--today", required=True, type=_date_arg)
    p.add_argument("--odometer", required=True, type=int)
    p.set_defaults(run=_due)

    p = sub.add_parser("check", help="faults in a trip log")
    p.add_argument("trips")
    p.set_defaults(run=_check)

    p = sub.add_parser("costs", help="running costs of one vehicle over a period")
    p.add_argument("vehicles")
    p.add_argument("fillups")
    p.add_argument("services")
    p.add_argument("--reg", required=True)
    p.add_argument("--from", dest="start", required=True, type=_date_arg)
    p.add_argument("--to", dest="end", required=True, type=_date_arg)
    p.set_defaults(run=_costs)
    return parser


def main(argv=None):
    """Run the command and return the exit status: 0 ok, 1 findings, 2 bad input."""
    args = _parser().parse_args(argv)
    try:
        return args.run(args)
    except FleetError as e:
        print(f"fleet: {e}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
