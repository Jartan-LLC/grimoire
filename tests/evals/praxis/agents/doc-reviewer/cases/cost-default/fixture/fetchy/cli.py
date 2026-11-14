"""fetchy URL: download URL into the current directory."""

import argparse
import pathlib
import urllib.request


def main() -> None:
    parser = argparse.ArgumentParser(prog="fetchy")
    parser.add_argument("url")
    args = parser.parse_args()
    with urllib.request.urlopen(args.url) as response:
        name = pathlib.PurePosixPath(args.url).name or "index.html"
        pathlib.Path(name).write_bytes(response.read())
