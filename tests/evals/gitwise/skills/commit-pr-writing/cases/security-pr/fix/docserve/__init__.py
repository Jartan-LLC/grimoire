"""Serve documents from a docs root."""

import pathlib

ROOT = pathlib.Path(__file__).parent / "docs"


def read_doc(name: str) -> str:
    """The text of document `name`; ValueError for a name outside the docs root."""
    path = (ROOT / name).resolve()
    if not path.is_relative_to(ROOT.resolve()):
        raise ValueError(name)
    return path.read_text()
