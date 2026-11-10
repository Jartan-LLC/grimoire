"""remindme add | snooze | list."""

import argparse
import sys
from datetime import datetime

from remindme.add import add_reminder
from remindme.snooze import snooze
from remindme.store import STORE, load


def main(argv: list[str]) -> int:
    """Run one command."""
    parser = argparse.ArgumentParser(prog="remindme")
    commands = parser.add_subparsers(dest="command", required=True)
    add = commands.add_parser("add", help="add a reminder")
    add.add_argument("text")
    add.add_argument("--in", dest="minutes", type=int, required=True, help="minutes from now")
    later = commands.add_parser("snooze", help="push a reminder back")
    later.add_argument("id", type=int)
    later.add_argument("duration", help="such as 10m, 1h30m or 2d")
    commands.add_parser("list", help="show reminders")
    args = parser.parse_args(argv)
    now = datetime.now()
    if args.command == "add":
        print(add_reminder(STORE, args.text, args.minutes, now)["id"])
    elif args.command == "snooze":
        snooze(STORE, args.id, args.duration, now)
    else:
        for item in load(STORE):
            print(f"{item['id']:>3}  {item['due']}  {item['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
