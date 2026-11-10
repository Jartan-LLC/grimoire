from notekeep.session import session_cookie


def test_cookie_carries_the_token():
    assert "session=abc" in session_cookie("abc")
