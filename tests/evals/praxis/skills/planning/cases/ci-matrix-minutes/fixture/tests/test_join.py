from pathkit import join


def test_join():
    assert join("a", "b") == "a/b"
