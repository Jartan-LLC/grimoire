from contactkit.model import Contact


def test_email_and_phone_are_optional():
    assert Contact("Ada") == Contact("Ada", None, None)
