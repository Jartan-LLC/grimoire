import argparse

from backupctl.store import prune


def main(argv=None):
    parser = argparse.ArgumentParser(prog="backupctl")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prune", help="delete all but the newest 7 backups")
    args = parser.parse_args(argv)
    if args.command == "prune":
        prune()
