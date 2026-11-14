from requests import Session

SESSION = Session()


def rate(pair: str) -> float:
    """The exchange rate for `pair`."""
    return SESSION.get(f"https://fx.example/{pair}", timeout=5).json()["rate"]
