from crm.merge import dedupe


def test_keeps_the_first_of_each():
    contacts = [{"email": "A@x.org"}, {"email": "b@x.org"}, {"email": " a@x.org"}]
    assert dedupe(contacts) == [{"email": "A@x.org"}, {"email": "b@x.org"}]
