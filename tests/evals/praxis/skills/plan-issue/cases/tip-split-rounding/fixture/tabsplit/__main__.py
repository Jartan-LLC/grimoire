"""python3 -m tabsplit TOTAL PEOPLE: print each person's share."""

import sys

from tabsplit.money import cents, show
from tabsplit.split import split


def main() -> None:
    """Read the total and the head count from the command line and print the shares."""
    total, people = cents(sys.argv[1]), int(sys.argv[2])
    for share in split(total, people):
        print(show(share))


if __name__ == "__main__":
    main()
