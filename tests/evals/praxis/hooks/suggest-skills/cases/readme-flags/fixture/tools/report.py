"""Print or save a sales report for a date range."""

import argparse
import csv
import json
import sys
from datetime import date

from tills.sales import sales_between


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--since", type=date.fromisoformat, required=True, help="first day, YYYY-MM-DD")
    parser.add_argument("--until", type=date.fromisoformat, default=date.today(), help="last day (default: today)")
    parser.add_argument("--format", choices=["csv", "json"], default="csv")
    parser.add_argument("--out", help="write the report to this file instead of standard output")
    parser.add_argument("--include-refunds", action="store_true", help="count refunds as negative sales")
    args = parser.parse_args()

    sales = sales_between(args.since, args.until, args.include_refunds)
    out = open(args.out, "w", newline="") if args.out else sys.stdout
    if args.format == "json":
        json.dump(sales, out, default=str)
    else:
        writer = csv.DictWriter(out, fieldnames=["day", "till", "amount"])
        writer.writeheader()
        writer.writerows(sales)


if __name__ == "__main__":
    main()
