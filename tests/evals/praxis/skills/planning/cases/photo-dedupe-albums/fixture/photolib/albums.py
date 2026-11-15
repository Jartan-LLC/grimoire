"""Read albums.json: album name -> list of photo paths."""

import json
import pathlib

ALBUMS = pathlib.Path("albums.json")


def load():
    return json.loads(ALBUMS.read_text())
