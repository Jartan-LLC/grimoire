import pathlib

from notes import load


def test_missing_file_is_empty(tmp_path: pathlib.Path) -> None:
    assert load(tmp_path / "none.json") == []
