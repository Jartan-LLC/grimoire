from slug import slug


def test_slug_uses_hyphens():
    assert slug("Hello World") == "hello-world"
