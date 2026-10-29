import json

import pytest

from bookapi.db import catalog


@pytest.fixture(autouse=True)
def small_catalog(tmp_path, monkeypatch):
    books = [{"id": i, "title": f"Book {i:03d}"} for i in range(1, 46)]
    authors = [{"id": i, "name": f"Author {i:03d}"} for i in range(1, 31)]
    path = tmp_path / "catalog.json"
    path.write_text(json.dumps({"books": books, "authors": authors}))
    monkeypatch.setenv("BOOKAPI_CATALOG", str(path))
    catalog.cache_clear()
