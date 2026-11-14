"""Import last month's payments from the bank's CSV."""

import csv
import sys

from billing.money import parse_amount

with open(sys.argv[1], newline="") as payments:
    for row in csv.reader(payments):
        print(row[0], parse_amount(row[2]))
