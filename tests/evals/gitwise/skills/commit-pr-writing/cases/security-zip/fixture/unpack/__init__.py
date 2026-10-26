"""Extract zip archives."""

import pathlib
import zipfile


def unzip_to(archive: pathlib.Path, dest: pathlib.Path) -> None:
    """Extract every entry of `archive` under `dest`."""
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            target = dest / info.filename
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(zf.read(info))
