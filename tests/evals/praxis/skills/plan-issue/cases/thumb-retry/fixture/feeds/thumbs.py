"""Download item thumbnails into the display's cache folder."""

import hashlib
import urllib.error
import urllib.request
from pathlib import Path


def download_thumb(url: str, cache: Path, timeout: float = 10.0) -> Path | None:
    """The cached thumbnail for `url`, downloading it first if needed; None when the download fails."""
    target = cache / (hashlib.sha256(url.encode()).hexdigest()[:16] + ".img")
    if target.exists():
        return target
    try:
        with urllib.request.urlopen(url, timeout=timeout) as response:
            target.write_bytes(response.read())
    except urllib.error.URLError:
        return None
    return target
