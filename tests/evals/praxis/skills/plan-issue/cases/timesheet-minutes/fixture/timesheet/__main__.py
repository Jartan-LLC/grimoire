"""python3 -m timesheet sheet.csv: print the hours of each week."""

import sys
from pathlib import Path

from timesheet.week import read_sheet, weekly_totals

for week, hours in sorted(weekly_totals(read_sheet(Path(sys.argv[1]))).items()):
    print(f"{week}  {hours:5.1f} h")
