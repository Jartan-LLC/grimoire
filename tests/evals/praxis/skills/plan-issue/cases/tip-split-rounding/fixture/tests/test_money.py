from tabsplit.money import cents, show


def test_cents_reads_two_decimals():
    assert cents("48.60") == 4860
    assert cents("7.5") == 750


def test_show_pads_cents():
    assert show(1205) == "12.05"
