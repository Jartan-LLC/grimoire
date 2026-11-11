from linkcheck.check import broken, check_all


def test_keeps_the_order_given():
    urls = ["https://a.example/x", "https://b.example/gone", "https://c.example/"]
    assert list(check_all(urls)) == urls


def test_reports_the_broken_ones():
    assert broken(["https://a.example/", "https://a.example/gone"]) == [
        "https://a.example/gone"
    ]
