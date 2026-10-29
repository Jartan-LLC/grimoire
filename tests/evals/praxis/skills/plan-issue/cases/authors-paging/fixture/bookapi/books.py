"""GET /books"""

from bookapi.db import catalog


def list_books(query: dict[str, str]) -> dict[str, object]:
    """One page of books, by title. ?page=1&per_page=20; per_page is capped at 100."""
    books = sorted(catalog()["books"], key=lambda b: str(b["title"]))
    try:
        page = max(int(query.get("page", 1)), 1)
        per_page = min(max(int(query.get("per_page", 20)), 1), 100)
    except ValueError:
        return {"error": "page and per_page must be whole numbers"}
    start = (page - 1) * per_page
    return {
        "items": books[start : start + per_page],
        "page": page,
        "per_page": per_page,
        "total": len(books),
    }
