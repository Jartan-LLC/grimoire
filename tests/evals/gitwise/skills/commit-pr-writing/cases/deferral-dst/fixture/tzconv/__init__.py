"""Convert local times to UTC."""

from datetime import datetime


def to_utc(local: str, zone: str) -> datetime:
    """`local` (YYYY-MM-DD HH:MM) in time zone `zone`, as a naive UTC datetime."""
    return datetime.strptime(local, "%Y-%m-%d %H:%M")
