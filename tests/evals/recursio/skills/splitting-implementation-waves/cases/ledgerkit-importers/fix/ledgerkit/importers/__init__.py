"""Bank export importers: one module per format, and `load` to pick one by sniffing."""

import os
from types import ModuleType

from ledgerkit.importers import camt053, mt940, ofx, qif
from ledgerkit.model import FormatError, ImportResult

FORMATS: dict[str, ModuleType] = {
    "camt053": camt053,
    "mt940": mt940,
    "ofx": ofx,
    "qif": qif,
}


def _read_text(path: str | os.PathLike[str]) -> str:
    with open(path, "rb") as handle:
        data = handle.read()
    try:
        return data.decode("utf-8")
    except UnicodeDecodeError:
        return data.decode("cp1252")


def load(path: str | os.PathLike[str]) -> ImportResult:
    """Read a file (UTF-8, else cp1252) and parse it with the first importer that sniffs it.

    Raises:
        FormatError: If no importer recognises the text.
    """
    text = _read_text(path)
    for module in FORMATS.values():
        if module.sniff(text):
            return module.parse(text)
    raise FormatError(f"unrecognised format: {os.fspath(path)}")
