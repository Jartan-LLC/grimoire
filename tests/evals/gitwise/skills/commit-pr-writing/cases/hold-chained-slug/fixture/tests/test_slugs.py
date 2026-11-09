from slugs import slugify


def test_spaces() -> None:
    assert slugify("a b") == "a-b"
