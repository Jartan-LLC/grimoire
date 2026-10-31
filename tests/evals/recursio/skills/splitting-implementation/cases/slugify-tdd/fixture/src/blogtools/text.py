"""Text helpers."""

import math


def word_count(text: str) -> int:
    return len(text.split())


def reading_time(text: str, words_per_minute: int = 220) -> int:
    """Whole minutes to read `text`, at least 1."""
    return max(1, math.ceil(word_count(text) / words_per_minute))
