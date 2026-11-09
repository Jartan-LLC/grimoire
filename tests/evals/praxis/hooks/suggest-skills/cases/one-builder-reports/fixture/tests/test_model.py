from reportkit.model import Table


def test_a_table_holds_its_rows():
    assert Table(["a"], [[1], [2]]).rows == [[1], [2]]
