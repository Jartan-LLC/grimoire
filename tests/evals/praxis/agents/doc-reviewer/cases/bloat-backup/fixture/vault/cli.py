"""The vault command line."""

import argparse
import sys

from vault import backup, store

USAGE = """\
vault init              make a vault in the current directory
vault status            show what changed since the last backup
vault backup DEST       write a dated .tar.gz archive of the vault into DEST
vault restore ARCHIVE   unpack ARCHIVE into the vault (default: the newest archive in DEST)
"""


def main() -> int:
    parser = argparse.ArgumentParser(prog="vault", usage=USAGE)
    parser.add_argument("command")
    parser.add_argument("arg", nargs="?")
    args = parser.parse_args()
    if args.command in ("backup", "restore") and not backup.tar_ok():
        print("vault: backup and restore need GNU or BusyBox tar", file=sys.stderr)
        return 2
    return getattr(store, args.command, getattr(backup, args.command))(args.arg)
