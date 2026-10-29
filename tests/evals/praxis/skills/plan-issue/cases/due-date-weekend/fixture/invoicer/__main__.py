"""Print the invoice for an order file: python3 -m invoicer order.json."""

import json
import sys
from datetime import date

from invoicer.render import render


def main() -> None:
    """Read the order named on the command line and print its invoice."""
    with open(sys.argv[1]) as handle:
        order = json.load(handle)
    print(render(order, date.today()))


if __name__ == "__main__":
    main()
