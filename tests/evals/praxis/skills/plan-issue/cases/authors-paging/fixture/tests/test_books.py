from bookapi.books import list_books


def test_second_page():
    body = list_books({"page": "2", "per_page": "20"})
    assert [b["id"] for b in body["items"]][:2] == [21, 22]
    assert body["total"] == 45


def test_per_page_is_capped():
    assert list_books({"per_page": "500"})["per_page"] == 100


def test_bad_page_is_an_error():
    assert "error" in list_books({"page": "two"})
