"""The dotfiles folder and the links into the home directory."""

import os
from pathlib import Path


def dots_dir() -> Path:
    """Where the dotfiles live: $DOTS_DIR, or ~/dotfiles."""
    return Path(os.environ.get("DOTS_DIR", Path.home() / "dotfiles"))


def managed() -> list[Path]:
    """Every dotfile in the folder, by name."""
    return sorted(p for p in dots_dir().iterdir() if p.is_file())


def link_all(home: Path) -> int:
    """Symlink each dotfile into `home`, replacing stale links; return how many were made."""
    made = 0
    for source in managed():
        target = home / source.name
        if target.is_symlink() and target.resolve() == source.resolve():
            continue
        if target.is_symlink():
            target.unlink()
        target.symlink_to(source)
        made += 1
    return made
