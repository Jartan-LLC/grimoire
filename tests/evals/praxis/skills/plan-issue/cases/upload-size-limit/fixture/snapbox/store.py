"""Where uploads land on the NAS."""

from datetime import datetime
from pathlib import Path

ALLOWED = {".jpg", ".jpeg", ".png", ".heic"}


class UploadRefused(Exception):
    """An upload the box does not keep; the message is shown in the phone app."""


def save_upload(root: Path, name: str, data: bytes, now: datetime | None = None) -> Path:
    """Save one upload under root/<year>/<month>/ and return its path."""
    suffix = Path(name).suffix.lower()
    if suffix not in ALLOWED:
        raise UploadRefused(f"{suffix or 'files without a type'} files are not accepted")
    when = now or datetime.now()
    folder = root / f"{when:%Y}" / f"{when:%m}"
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / Path(name).name
    target.write_bytes(data)
    return target
