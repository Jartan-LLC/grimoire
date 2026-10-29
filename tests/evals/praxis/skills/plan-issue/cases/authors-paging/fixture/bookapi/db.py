"""The catalog, loaded once from catalog.json: {"books": [...], "authors": [...]}."""

import json
import os
from functools import cache
from pathlib import Path


@cache
def catalog() -> dict[str, list[dict[str, object]]]:
    """The whole catalog; $BOOKAPI_CATALOG names the file."""
    return json.loads(Path(os.environ.get("BOOKAPI_CATALOG", "catalog.json")).read_text())
