"""Fetch exchange rates."""

import json
import urllib.request
from collections.abc import Callable

URL = "https://rates.example.com/latest"


def fetch_rates(opener: Callable[..., object] = urllib.request.urlopen) -> dict[str, float]:
    """The latest rates."""
    with opener(URL, timeout=5) as response:  # type: ignore[attr-defined]
        return json.loads(response.read())
