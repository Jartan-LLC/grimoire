"""python3 -m fxconv <amount> <from> <to>"""

import sys
from decimal import Decimal

from fxconv.rates import convert, fetch_rates


def main(argv: list[str]) -> int:
    """Print the converted amount, rounded to cents."""
    if len(argv) != 3:
        print("usage: fxconv <amount> <from> <to>", file=sys.stderr)
        return 2
    amount, source, target = Decimal(argv[0]), argv[1].upper(), argv[2].upper()
    rates = fetch_rates(source)
    print(f"{convert(amount, rates[target]):.2f} {target}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
