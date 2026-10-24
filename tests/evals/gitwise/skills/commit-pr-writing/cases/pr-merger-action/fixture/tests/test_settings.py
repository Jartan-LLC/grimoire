import pathlib

from settings import load


def test_load(tmp_path: pathlib.Path) -> None:
    (tmp_path / "s.json").write_text("{}")
    assert load(tmp_path / "s.json") == {}
