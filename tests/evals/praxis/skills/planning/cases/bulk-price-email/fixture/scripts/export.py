"""Print every customer account as CSV."""
import csv
import os
import sys

import psycopg

with psycopg.connect(os.environ["DATABASE_URL"]) as conn:
    rows = conn.execute("SELECT id, email, name, plan, status FROM accounts ORDER BY id")
    out = csv.writer(sys.stdout)
    out.writerow(["id", "email", "name", "plan", "status"])
    out.writerows(rows)
