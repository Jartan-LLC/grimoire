"""URL slugs."""

import re


def slugify(text: str) -> str:
    """Return `text` lower-cased with runs of non-alphanumerics turned into one hyphen."""
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")
