from stockroom.api import stock_level
from stockroom.store import Store


def test_stock_level_of_a_stocked_sku() -> None:
    store = Store()
    store.put("a", 4)
    assert stock_level(store, "a") == 4
