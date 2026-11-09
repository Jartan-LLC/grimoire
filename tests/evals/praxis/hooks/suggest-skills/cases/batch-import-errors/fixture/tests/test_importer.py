from orders.importer import Order, import_batch


def test_reads_every_line():
    assert import_batch(["o1,A,2", "o2,B,1"]) == [Order("o1", "A", 2), Order("o2", "B", 1)]
