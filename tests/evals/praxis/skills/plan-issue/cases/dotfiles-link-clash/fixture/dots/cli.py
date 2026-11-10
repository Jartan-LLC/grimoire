"""The `dots` command."""

import argparse
from pathlib import Path

from dots import files


def main(argv: list[str] | None = None) -> None:
    """Run one subcommand."""
    parser = argparse.ArgumentParser(prog="dots")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("list", help="list the managed dotfiles")
    sub.add_parser("link", help="symlink every dotfile into your home directory")
    sub.add_parser("status", help="show missing or foreign links")
    args = parser.parse_args(argv)
    home = Path.home()

    if args.command == "list":
        for path in files.managed():
            print(path.name)
    elif args.command == "link":
        print(f"linked {files.link_all(home)} dotfiles")
    elif args.command == "status":
        for path in files.managed():
            target = home / path.name
            if not (target.is_symlink() and target.resolve() == path.resolve()):
                print(f"not linked: {path.name}")
