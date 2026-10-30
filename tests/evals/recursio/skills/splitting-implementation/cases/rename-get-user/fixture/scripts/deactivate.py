"""Deactivate the users given on the command line."""

import sys

from crm.admin import deactivate
from crm.users import get_user

for arg in sys.argv[1:]:
    if get_user(int(arg)) and deactivate(int(arg)):
        print(f"deactivated {arg}")
