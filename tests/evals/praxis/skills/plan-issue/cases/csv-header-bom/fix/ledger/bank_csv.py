"""Read a bank's statement export."""

import csv
from decimal import Decimal
from pathlib import Path


def read_statement(path: Path) -> list[dict[str, object]]:
    """Each row's date, payee and amount; the file has a header row: date,payee,amount."""
    with path.open(newline="", encoding="utf-8-sig") as handle:
        return [
            {"date": row["date"], "payee": row["payee"].strip(), "amount": Decimal(row["amount"])}
            for row in csv.DictReader(handle)
        ]
