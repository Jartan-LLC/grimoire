import pathlib
import zipfile

from unpack import unzip_to


def test_extracts(tmp_path: pathlib.Path) -> None:
    archive = tmp_path / "a.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("x.txt", "hi")
    unzip_to(archive, tmp_path / "out")
    assert (tmp_path / "out" / "x.txt").read_text() == "hi"
