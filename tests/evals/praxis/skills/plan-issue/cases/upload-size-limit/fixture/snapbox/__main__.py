"""Serve uploads: python3 -m snapbox."""

from http.server import ThreadingHTTPServer
from pathlib import Path

from snapbox.server import make_handler

ROOT = Path("/srv/photos")


def main() -> None:
    """Serve until stopped."""
    ThreadingHTTPServer(("", 8420), make_handler(ROOT)).serve_forever()


if __name__ == "__main__":
    main()
