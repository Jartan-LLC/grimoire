from members.load import Member, load_members


def test_loads_each_member():
    lines = ["Ann Lee,ann@example.org,2019\n", "\n", "Bo Ek,bo@example.org,2021\n"]
    assert load_members(lines) == [
        Member("Ann Lee", "ann@example.org", 2019),
        Member("Bo Ek", "bo@example.org", 2021),
    ]
