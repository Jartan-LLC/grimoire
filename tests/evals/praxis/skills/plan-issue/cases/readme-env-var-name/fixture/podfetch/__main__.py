"""python3 -m podfetch FEEDS_FILE."""

import sys

from podfetch.feeds import read_feeds
from podfetch.settings import download_dir, limit


def main() -> None:
    """Print where each feed's episodes would go; fetching lives in podfetch.fetch."""
    for url in read_feeds(sys.argv[1]):
        print(f"{url} -> {download_dir()} (newest {limit()})")


if __name__ == "__main__":
    main()
