"""Bibliographies: read and write BibTeX and RIS, format references, and merge duplicates."""

from .model import MONTHS, Entry, EntryType, Name, ParseError, ParseResult

__all__ = ["MONTHS", "Entry", "EntryType", "Name", "ParseError", "ParseResult"]
