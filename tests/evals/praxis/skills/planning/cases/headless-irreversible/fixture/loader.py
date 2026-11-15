import json
import pathlib

DATA = pathlib.Path(__file__).parent / "data" / "users.json"


def users():
    return json.loads(DATA.read_text())


def display_name(user):
    return user["name"]
