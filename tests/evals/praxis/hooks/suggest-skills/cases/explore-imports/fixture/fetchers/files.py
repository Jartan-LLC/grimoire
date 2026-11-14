import pathlib


def read(path: str) -> str:
    """A local file's text."""
    return pathlib.Path(path).read_text()
