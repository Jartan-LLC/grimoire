"""Import last month's payments from the bank's CSV."""

import csv
import sys

from billing.money import parse_amount

for row in csv.reader(open(sys.argv[1])):
    print(row[0], parse_amount(row[2]))
