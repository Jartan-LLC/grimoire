"""Pagination helpers."""


def page_count(items: int, per_page: int) -> int:
    """How many pages `items` items fill at `per_page` a page."""
    return items // per_page + 1
