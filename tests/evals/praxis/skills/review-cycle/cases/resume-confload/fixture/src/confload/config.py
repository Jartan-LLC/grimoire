"""Load the app's settings from a TOML file."""

import tomllib

DEFAULT_PATH = "confload.toml"
UNITS = {"s": 1, "m": 60, "h": 3600}


def parse_window(text):
    """Seconds in a duration such as "30s" or "5m"."""
    return int(text[:-1]) * UNITS[text[-1]]


def load_config(path=DEFAULT_PATH):
    """The settings in `path`, with `window` turned into seconds."""
    with open(path, "rb") as handle:
        data = tomllib.load(handle)
    if "window" in data:
        data["window"] = parse_window(data["window"])
    return data
