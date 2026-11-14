from stocktake.alerts import low_items


def test_low_items_lists_the_short_ones():
    cfg = {"low_stock_threshold": 5}
    assert low_items({"tape": 2, "boxes": 40}, cfg) == ["tape"]
