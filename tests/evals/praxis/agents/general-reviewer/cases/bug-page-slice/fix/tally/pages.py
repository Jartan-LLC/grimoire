"""Show an export a page at a time."""

from tally.parse import parse_rows


def page(text: str, number: int, size: int = 25) -> list[dict[str, str]]:
    """The rows on page `number` (counting from 1), `size` rows to a page."""
    rows = parse_rows(text)
    start = (number - 1) * size
    return rows[start : start + size]
