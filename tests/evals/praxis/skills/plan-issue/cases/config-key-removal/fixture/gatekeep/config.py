"""Read config.toml. An unknown key stops the start-up, so a typo is never silently ignored."""

import tomllib

KEYS = {"listen", "upstream", "legacy_auth"}


def load(path):
    with open(path, "rb") as f:
        data = tomllib.load(f)
    unknown = set(data) - KEYS
    if unknown:
        raise SystemExit(f"config.toml: unknown keys {sorted(unknown)}")
    return data
