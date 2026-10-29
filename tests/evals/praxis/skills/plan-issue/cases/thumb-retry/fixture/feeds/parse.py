"""Pull items out of RSS XML."""

import xml.etree.ElementTree as ET


def items(xml: bytes) -> list[dict[str, str | None]]:
    """Each item's title, link and thumbnail URL (media:thumbnail), in feed order."""
    media = "{http://search.yahoo.com/mrss/}thumbnail"
    found = []
    for item in ET.fromstring(xml).iter("item"):
        thumb = item.find(media)
        found.append({
            "title": item.findtext("title", ""),
            "link": item.findtext("link", ""),
            "thumb": thumb.get("url") if thumb is not None else None,
        })
    return found
