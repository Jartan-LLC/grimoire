import sqlite3

from reports.export import export_rows


def make_db(path, rows):
    connection = sqlite3.connect(path)
    connection.execute("CREATE TABLE sales (name TEXT, amount REAL)")
    connection.executemany("INSERT INTO sales VALUES (?, ?)", rows)
    connection.commit()
    connection.close()


def test_writes_every_sale(tmp_path):
    db = tmp_path / "sales.db"
    make_db(db, [("tea", 3.5), ("cake", 4.0)])
    out = tmp_path / "out.tsv"
    assert export_rows(str(db), str(out)) == 2
    assert out.read_text() == "cake\t4.00\ntea\t3.50\n"
