"""The hivekit command."""

import argparse
import sys
from datetime import date
from pathlib import Path

from hivekit.health import flags, overdue
from hivekit.honey import honey_kg
from hivekit.log import LogError, by_hive, parse_log


def main(argv: list[str] | None = None) -> int:
    """Run the hivekit command; return its exit status."""
    parser = argparse.ArgumentParser(prog="hivekit")
    commands = parser.add_subparsers(dest="command", required=True)
    status = commands.add_parser("status")
    status.add_argument("log")
    status.add_argument("--today", type=date.fromisoformat, required=True)
    honey = commands.add_parser("honey")
    honey.add_argument("log")
    args = parser.parse_args(argv)
    try:
        log = parse_log(Path(args.log).read_text())
    except (OSError, LogError) as error:
        print(f"hivekit: {error}", file=sys.stderr)
        return 2
    hives = by_hive(log)
    if args.command == "status":
        late = set(overdue(log, args.today))
        for hive, history in hives.items():
            mark = " (overdue)" if hive in late else ""
            print(f"{hive} {history[-1].date.isoformat()} {','.join(flags(history)) or 'ok'}{mark}")
    else:
        for hive, history in hives.items():
            print(f"{hive} {honey_kg(history[-1]):.1f}")
    return 0
