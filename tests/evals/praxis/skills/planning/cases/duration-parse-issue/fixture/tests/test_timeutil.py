from timeutil import format_duration


def test_format_duration():
    assert format_duration(5400) == "1h30m"
