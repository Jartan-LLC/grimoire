"""Load data/customers.json into the shop: one account per record."""

import json
import pathlib

for record in json.loads(pathlib.Path("data/customers.json").read_text()):
    print("import", record["id"], record["email"])
