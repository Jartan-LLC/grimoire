"""brewlog: `brewlog add <date> <name> <style>` and `brewlog list`."""

import argparse

from brewlog import storage


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="brewlog")
    sub = parser.add_subparsers(dest="command", required=True)
    add = sub.add_parser("add")
    add.add_argument("date")
    add.add_argument("name")
    add.add_argument("style")
    sub.add_parser("list")
    args = parser.parse_args(argv)
    file = storage.path()
    if args.command == "add":
        storage.append(file, {"date": args.date, "name": args.name, "style": args.style})
    else:
        for brew in storage.load(file):
            print(f"{brew['date']}  {brew['name']} ({brew['style']})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
