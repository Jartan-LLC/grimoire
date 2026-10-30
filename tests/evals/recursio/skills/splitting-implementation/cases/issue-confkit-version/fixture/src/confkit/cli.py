"""The confkit command."""

import argparse
import tomllib


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="confkit")
    sub = parser.add_subparsers(dest="command", required=True)
    check = sub.add_parser("check")
    check.add_argument("file")
    args = parser.parse_args(argv)
    try:
        with open(args.file, "rb") as handle:
            tomllib.load(handle)
    except (OSError, tomllib.TOMLDecodeError) as error:
        print(f"{args.file}: {error}")
        return 1
    print(f"{args.file}: ok")
    return 0
