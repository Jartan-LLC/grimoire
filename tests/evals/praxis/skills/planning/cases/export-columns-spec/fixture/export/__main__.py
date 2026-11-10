import sys

from export.orders import write_month

if sys.argv[1] == "orders":
    write_month(sys.argv[3])
