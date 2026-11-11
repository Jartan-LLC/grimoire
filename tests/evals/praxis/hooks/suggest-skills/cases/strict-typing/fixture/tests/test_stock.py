from inventory.stock import Stock, group_by_location


def test_totals_across_locations():
    stock = Stock()
    stock.add("A", "north", 2)
    stock.add("A", "south", 3)
    stock.add("B", "north", 1)
    assert stock.total("A") == 5
    assert stock.lowest(1) == ["B"]


def test_group_by_location():
    assert group_by_location([("A", "n", 1), ("B", "n", 2)]) == {"n": [("A", 1), ("B", 2)]}
