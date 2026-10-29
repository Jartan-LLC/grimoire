from pantry.quantity import format_quantity, parse_quantity


def test_mixed_number():
    assert parse_quantity("1 1/2") == 1.5


def test_whole_amount_prints_bare():
    assert format_quantity(2.0) == "2"
    assert format_quantity(0.5) == "0.5"
