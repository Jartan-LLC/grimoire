"""Where clipper keeps its files."""

import os
import pathlib


def settings_file() -> pathlib.Path:
    """`$CLIPPER_CONFIG`, else `$XDG_CONFIG_HOME/clipper/settings.toml`, else ~/.config."""
    if explicit := os.environ.get("CLIPPER_CONFIG"):
        return pathlib.Path(explicit)
    base = os.environ.get("XDG_CONFIG_HOME") or pathlib.Path.home() / ".config"
    return pathlib.Path(base) / "clipper" / "settings.toml"
