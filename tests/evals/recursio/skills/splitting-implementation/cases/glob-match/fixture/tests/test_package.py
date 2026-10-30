import pathglob


def test_package_exports_match():
    assert pathglob.__all__ == ["match"]
