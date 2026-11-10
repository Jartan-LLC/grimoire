from billing.invoice import sum_lines


def test_sum_lines():
    assert sum_lines([{"qty": 2, "price": 3}]) == 6
