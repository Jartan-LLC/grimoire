import csv

from stocktake.alerts import low_items, send_alert
from stocktake.settings import load

cfg = load()
with open("stock.csv", newline="") as f:
    stock = {row["item"]: int(row["count"]) for row in csv.DictReader(f)}
items = low_items(stock, cfg)
if items:
    send_alert(items, cfg)
