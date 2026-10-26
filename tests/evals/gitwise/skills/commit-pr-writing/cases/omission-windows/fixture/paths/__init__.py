"""Path helpers."""


def normalize(path: str) -> str:
    """`path` with a trailing slash removed."""
    return path.rstrip("/") or "/"
