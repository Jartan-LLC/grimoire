from bookapi.authors import list_authors


def test_sorted_by_name():
    names = [a["name"] for a in list_authors({})["items"]]
    assert names == sorted(names)
