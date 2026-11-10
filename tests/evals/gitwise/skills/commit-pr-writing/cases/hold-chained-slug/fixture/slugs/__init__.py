"""URL slugs."""

import re


def slugify(title: str) -> str:
    """Lower-case `title`, with each run of other characters turned into one hyphen."""
    return re.sub(r"[^a-z0-9]+", "-", title.lower()).lstrip("-")
