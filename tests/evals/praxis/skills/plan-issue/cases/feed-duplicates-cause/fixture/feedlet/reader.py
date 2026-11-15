"""Fetch every feed and merge their posts, newest first."""

import urllib.request
import xml.etree.ElementTree as ET


def posts(url):
    with urllib.request.urlopen(url, timeout=10) as resp:
        root = ET.parse(resp).getroot()
    for item in root.iter("item"):
        yield {"title": item.findtext("title"), "guid": item.findtext("guid"),
               "date": item.findtext("pubDate")}


def newest(urls):
    merged = [p for url in urls for p in posts(url)]
    return sorted(merged, key=lambda p: p["date"], reverse=True)
