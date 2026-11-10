"""The backup folder: one file per night, named by date."""

import pathlib

ROOT = pathlib.Path("/var/backups/db")


def prune(keep=7):
    for old in sorted(ROOT.glob("*.dump"), reverse=True)[keep:]:
        old.unlink()
