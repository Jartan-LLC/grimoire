"""GET /authors"""

from bookapi.db import catalog


def list_authors(query: dict[str, str]) -> dict[str, object]:
    """Every author, by name."""
    return {"items": sorted(catalog()["authors"], key=lambda a: str(a["name"]))}
