from bibkit import MONTHS, Entry, EntryType, Name, ParseError


def test_a_particle_is_not_part_of_the_family_name():
    name = Name(family="Waals", given="Johannes", von="van der")
    assert name.family == "Waals"
    assert name.jr == ""


def test_a_new_entry_has_no_fields_or_people():
    entry = Entry("waals1873", EntryType.PHDTHESIS)
    assert entry.fields == {}
    assert entry.authors == [] and entry.editors == []
    assert MONTHS[0] == "January" and len(MONTHS) == 12


def test_a_parse_error_carries_its_line():
    err = ParseError("unterminated value", 12)
    assert err.line == 12
    assert str(err) == "line 12: unterminated value"
