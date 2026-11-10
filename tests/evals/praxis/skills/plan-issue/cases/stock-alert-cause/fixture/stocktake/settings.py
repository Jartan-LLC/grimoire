"""Read settings.json from the folder the cron job runs in."""

import json


def load(path="settings.json"):
    with open(path) as f:
        return json.load(f)
