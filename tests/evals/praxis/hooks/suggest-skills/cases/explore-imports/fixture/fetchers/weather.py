import requests


def today(city: str) -> dict:
    """Today's weather in `city`."""
    return requests.get(f"https://w.example/{city}", timeout=5).json()
