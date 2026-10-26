"""Convert local times to UTC."""

from datetime import UTC, datetime
from zoneinfo import ZoneInfo


def to_utc(local: str, zone: str) -> datetime:
    """`local` (YYYY-MM-DD HH:MM) in time zone `zone`, as a naive UTC datetime."""
    stamp = datetime.strptime(local, "%Y-%m-%d %H:%M").replace(tzinfo=ZoneInfo(zone))
    return stamp.astimezone(UTC).replace(tzinfo=None)
