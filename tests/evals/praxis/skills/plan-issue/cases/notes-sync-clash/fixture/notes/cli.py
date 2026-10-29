"""The `notes` command."""

import argparse

from notes import backup, store


def main(argv: list[str] | None = None) -> None:
    """Run one subcommand."""
    parser = argparse.ArgumentParser(prog="notes")
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add", help="add a note")
    add.add_argument("title")
    add.add_argument("text")
    sub.add_parser("list", help="list notes")
    show = sub.add_parser("show", help="print a note")
    show.add_argument("id", type=int)
    sub.add_parser("sync", help="copy every note to the backup folder")
    args = parser.parse_args(argv)

    if args.command == "add":
        print(store.add(args.title, args.text))
    elif args.command == "list":
        for note_id, title in store.all_notes():
            print(f"{note_id:>4}  {title}")
    elif args.command == "show":
        print(store.read(args.id), end="")
    elif args.command == "sync":
        print(f"copied {backup.copy_all()} notes")
