"""Text statistics."""


def word_count(text: str) -> int:
    """Words in `text`, separated by whitespace."""
    return len(text.split())
