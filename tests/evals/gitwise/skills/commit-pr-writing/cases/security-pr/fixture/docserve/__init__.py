"""Serve documents from a docs root."""

import pathlib

ROOT = pathlib.Path(__file__).parent / "docs"


def read_doc(name: str) -> str:
    """The text of document `name`."""
    return (ROOT / name).read_text()
