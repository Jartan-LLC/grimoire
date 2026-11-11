"""Print the counts for each file named on the command line."""

import sys

from wordcount.count import count


def main(argv: list[str]) -> int:
    """Print one line per file; return the exit status."""
    for path in argv:
        with open(path) as f:
            c = count(f.read())
        print(f"{c.lines:>8}{c.words:>8}{c.chars:>8} {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
