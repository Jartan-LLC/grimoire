"""Read pingmon.toml."""

import tomllib

KEYS = {"url": str, "interval_s": int, "timeout_s": int, "retries": int}
DEFAULTS = {"interval_s": 60, "timeout_s": 10, "retries": 0}


class ConfigError(ValueError):
    """A config file pingmon cannot use."""


def parse(text: str) -> list[dict[str, object]]:
    """Every [[check]] in the config, with defaults filled in."""
    checks = []
    for raw in tomllib.loads(text).get("check", []):
        for key, value in raw.items():
            if key not in KEYS:
                raise ConfigError(f"unknown key {key!r}")
            if not isinstance(value, KEYS[key]):
                raise ConfigError(f"{key} must be {KEYS[key].__name__}")
        if "url" not in raw:
            raise ConfigError("every check needs a url")
        checks.append({**DEFAULTS, **raw})
    return checks
