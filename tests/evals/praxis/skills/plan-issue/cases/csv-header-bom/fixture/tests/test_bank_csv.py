from decimal import Decimal

from ledger.bank_csv import read_statement


def test_reads_rows(tmp_path):
    path = tmp_path / "s.csv"
    path.write_text("date,payee,amount\n2026-10-01, Grocer ,-23.50\n")
    assert read_statement(path) == [
        {"date": "2026-10-01", "payee": "Grocer", "amount": Decimal("-23.50")}
    ]
