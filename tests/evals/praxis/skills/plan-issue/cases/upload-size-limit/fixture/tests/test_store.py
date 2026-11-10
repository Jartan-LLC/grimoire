from datetime import datetime

import pytest

from snapbox.store import UploadRefused, save_upload


def test_saves_by_month(tmp_path):
    saved = save_upload(tmp_path, "beach.JPG", b"jpeg", now=datetime(2026, 8, 14))
    assert saved == tmp_path / "2026" / "08" / "beach.JPG"
    assert saved.read_bytes() == b"jpeg"


def test_refuses_other_types(tmp_path):
    with pytest.raises(UploadRefused, match=".exe files are not accepted"):
        save_upload(tmp_path, "setup.exe", b"MZ")
