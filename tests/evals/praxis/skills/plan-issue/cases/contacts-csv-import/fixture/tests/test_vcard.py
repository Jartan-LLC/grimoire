from rolodex.models import make_contact
from rolodex.vcard import to_vcard


def test_vcard_without_phone():
    card = to_vcard(make_contact("Ada", "ada@example.com"))
    assert "TEL" not in card
    assert card.startswith("BEGIN:VCARD\r\nVERSION:3.0")
