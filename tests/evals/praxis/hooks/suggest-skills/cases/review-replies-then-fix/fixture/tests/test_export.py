import csv
from decimal import Decimal

from reports.export import export_csv


def test_writes_a_row_per_invoice(tmp_path):
    path = tmp_path / "march.csv"
    export_csv(str(path), [{"id": 7, "customer": "Acme", "amount": Decimal("12.5")}])
    rows = list(csv.reader(path.open()))
    assert rows == [["invoice", "customer", "amount"], ["7", "Acme", "12.50"]]
