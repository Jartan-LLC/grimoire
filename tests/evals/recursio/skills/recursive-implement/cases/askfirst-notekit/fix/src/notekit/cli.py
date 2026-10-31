# SPDX-License-Identifier: MIT
"""The notekit command."""

import argparse

from notekit.links import backlinks, broken
from notekit.notes import load_notes
from notekit.tags import tag_index


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="notekit")
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("tags").add_argument("folder")
    back = commands.add_parser("backlinks")
    back.add_argument("folder")
    back.add_argument("note")
    commands.add_parser("broken").add_argument("folder")
    args = parser.parse_args(argv)
    notes = load_notes(args.folder)
    if args.command == "tags":
        for tag, names in tag_index(notes).items():
            print(f"{tag}: {', '.join(names)}")
        return 0
    if args.command == "backlinks":
        index = backlinks(notes)
        if args.note not in index:
            return 1
        for name in index[args.note]:
            print(name)
        return 0
    found = broken(notes)
    for note, target in found:
        print(f"{note} -> {target}")
    return 1 if found else 0
