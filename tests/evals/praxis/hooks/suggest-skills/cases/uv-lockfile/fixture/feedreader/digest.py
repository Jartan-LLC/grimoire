"""Render the day's entries."""


def title_line(title: str, source: str) -> str:
    """One line of the digest."""
    return f"- {title} ({source})"
