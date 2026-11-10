from temps import c_to_f


def test_boiling() -> None:
    assert c_to_f(100) == 212
