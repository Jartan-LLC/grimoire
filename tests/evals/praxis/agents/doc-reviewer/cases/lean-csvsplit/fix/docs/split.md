# Split a CSV file

`csvsplit orders.csv` writes `orders.1.csv`, `orders.2.csv` and so on, each with the header row.
Each part holds 1000 rows unless you pass `--rows N`.
