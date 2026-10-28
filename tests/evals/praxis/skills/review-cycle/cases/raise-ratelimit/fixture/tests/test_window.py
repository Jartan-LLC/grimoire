from ratelimit import SlidingWindow, parse_window


def test_parse_window():
    assert parse_window("10/m") == (10, 60)


def test_allow_up_to_the_limit():
    now = [0.0]
    window = SlidingWindow("2/s", clock=lambda: now[0])
    assert window.allow()
    assert window.allow()
    assert not window.allow()
    now[0] = 1.5
    assert window.allow()
