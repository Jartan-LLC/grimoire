"""Refresh every feed and its thumbnails: run by cron every ten minutes."""

from pathlib import Path

from feeds.fetch import fetch_feed
from feeds.parse import items
from feeds.thumbs import download_thumb


def refresh(urls: list[str], cache: Path) -> list[dict[str, str | None]]:
    """Every item of every feed, each with `thumb_path` set when its thumbnail is cached."""
    out = []
    for url in urls:
        for item in items(fetch_feed(url)):
            path = download_thumb(item["thumb"], cache) if item["thumb"] else None
            out.append({**item, "thumb_path": str(path) if path else None})
    return out
