from crm.users import get_user


def test_known_and_unknown():
    assert get_user(1).name == "Ada"
    assert get_user(99) is None
