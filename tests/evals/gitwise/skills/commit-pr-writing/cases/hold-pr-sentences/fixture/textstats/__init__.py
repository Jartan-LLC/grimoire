"""Text statistics."""


def word_count(text: str) -> int:
    """Words in `text`, split on whitespace."""
    return len(text.split())
