# Using csvstats

Summarise every numeric column:

```bash
python3 -m csvstats sales.csv
```

Summarise one column of a semicolon-separated export:

```bash
python3 -m csvstats sales.csv --col price --sep ';'
```

Empty cells are skipped. A column with any other non-numeric cell is left out of the summary.
