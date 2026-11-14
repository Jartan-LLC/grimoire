"""Find the photos in the library."""

import pathlib

LIBRARY = pathlib.Path("library")


def photos():
    return sorted(p for p in LIBRARY.rglob("*.jpg") if p.is_file())
