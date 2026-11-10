import json
import urllib.request

BASE = "https://shop.example.com/api/orders"


def fetch_page(page, size):
    url = f"{BASE}?page={page}&size={size}"
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)
