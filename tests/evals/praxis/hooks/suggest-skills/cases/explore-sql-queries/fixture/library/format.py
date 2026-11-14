"""Display helpers."""


def shelfmark(code: str) -> str:
    """A shelfmark as printed on the spine."""
    return code.upper().replace("-", " ")
