import json
import urllib.request

BASE = "https://vendor.example.com"


def get(url):
    with urllib.request.urlopen(url, timeout=30) as resp:
        return json.load(resp)
