"""Export sales rows to a text file."""

import sqlite3


def format_row(row: tuple[str, float]) -> str:
    """One line of the export."""
    name, amount = row
    if amount < 0:
        raise ValueError(f"{name}: negative amount {amount}")
    return f"{name}\t{amount:.2f}\n"


def export_rows(db_path: str, out_path: str) -> int:
    """Write every sale in `db_path` to `out_path`; return how many."""
    connection = sqlite3.connect(db_path)
    out = open(out_path, "w")
    count = 0
    for row in connection.execute("SELECT name, amount FROM sales ORDER BY name"):
        out.write(format_row(row))
        count += 1
    out.close()
    connection.close()
    return count
