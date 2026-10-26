"""Word statistics for plain text."""


def word_count(text: str) -> int:
    """The number of words in `text`, split on whitespace; a hyphenated word counts once."""
    return len(text.split())
