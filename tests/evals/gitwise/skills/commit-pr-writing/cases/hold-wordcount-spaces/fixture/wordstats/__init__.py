"""Text statistics."""


def word_count(text: str) -> int:
    """Words in `text`, separated by spaces."""
    return len(text.split(" "))
