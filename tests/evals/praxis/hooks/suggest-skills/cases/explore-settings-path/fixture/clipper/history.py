"""The clipboard history."""

HISTORY: list[str] = []


def push(text: str) -> None:
    """Remember `text`."""
    HISTORY.append(text)
