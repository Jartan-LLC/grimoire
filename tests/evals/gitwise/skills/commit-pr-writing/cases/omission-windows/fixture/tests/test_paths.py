from paths import normalize


def test_trailing_slash() -> None:
    assert normalize("a/b/") == "a/b"
