from csvstats.cli import main


def test_one_column(tmp_path, capsys):
    sheet = tmp_path / "sales.csv"
    sheet.write_text("item;price;qty\ntea;4.5;2\nhoney;7.99;\n")
    main([str(sheet), "--col", "price", "--sep", ";"])
    assert capsys.readouterr().out == "price: count 2  mean 6.25  min 4.5  max 7.99\n"


def test_text_columns_are_left_out(tmp_path, capsys):
    sheet = tmp_path / "sales.csv"
    sheet.write_text("item,price\ntea,4.5\n")
    main([str(sheet)])
    assert capsys.readouterr().out.startswith("price:")
