"""Build this case's history: run by the eval runner inside the fixture repository."""

import json
import pathlib

USERS = [
    {"id": 1, "name": "Ada Lovelace", "email": "ada@example.com"},
    {"id": 2, "name": "Grace Brewster Murray Hopper", "email": "grace@example.com"},
    {"id": 3, "name": "Cher", "email": "cher@example.com"},
    {"id": 4, "name": "Ludwig van Beethoven", "email": "lvb@example.com"},
]
data = pathlib.Path("data")
data.mkdir(exist_ok=True)
(data / "users.json").write_text(json.dumps(USERS, indent=2) + "\n")
