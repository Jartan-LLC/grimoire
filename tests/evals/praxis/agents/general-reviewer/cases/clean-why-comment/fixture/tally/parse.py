"""Read the shop's CSV export into rows."""

import csv
import io


def parse_rows(text: str) -> list[dict[str, str]]:
    """The export's data rows, keyed by header, with blank lines skipped."""
    text = text.removeprefix("\ufeff")
    return [row for row in csv.DictReader(io.StringIO(text)) if any(row.values())]
