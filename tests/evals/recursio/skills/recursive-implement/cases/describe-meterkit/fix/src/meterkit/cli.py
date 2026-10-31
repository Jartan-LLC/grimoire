# SPDX-License-Identifier: MIT
"""The meterkit command."""

import argparse
import sys
from decimal import Decimal

from meterkit.anomaly import anomalies
from meterkit.readings import ReadingError, intervals, parse_readings
from meterkit.tariff import Tariff, bill

TIME = "%Y-%m-%dT%H:%M"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="meterkit")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("usage").add_argument("file")
    billing = commands.add_parser("bill")
    billing.add_argument("file")
    for option in ("--peak", "--offpeak", "--standing"):
        billing.add_argument(option, type=Decimal, required=True)
    billing.add_argument("--meter")
    finding = commands.add_parser("anomalies")
    finding.add_argument("file")
    finding.add_argument("--factor", type=Decimal, default=Decimal(3))
    args = parser.parse_args(argv)
    try:
        with open(args.file) as handle:
            spans = intervals(parse_readings(handle.read()))
    except (OSError, ReadingError) as error:
        print(f"meterkit: {error}", file=sys.stderr)
        return 2
    if args.command == "usage":
        for i in spans:
            print(f"{i.meter} {i.start:{TIME}} {i.end:{TIME}} {i.kwh:.3f}")
    elif args.command == "bill":
        chosen = [i for i in spans if args.meter in (None, i.meter)]
        result = bill(chosen, Tariff(args.peak, args.offpeak, args.standing))
        print(f"peak_kwh: {result.peak_kwh:.3f}")
        print(f"offpeak_kwh: {result.offpeak_kwh:.3f}")
        print(f"days: {result.days}")
        print(f"total: {result.total:.2f}")
    else:
        for a in anomalies(spans, args.factor):
            print(f"{a.interval.meter} {a.interval.start:{TIME}} {a.interval.kwh:.3f} {a.median:.3f}")
    return 0
