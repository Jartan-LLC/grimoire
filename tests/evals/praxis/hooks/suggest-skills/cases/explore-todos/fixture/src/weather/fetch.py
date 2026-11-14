"""Fetch a forecast from the provider."""


def forecast_url(lat: float, lon: float) -> str:
    """The provider's URL for a point."""
    # TODO: round to the provider's 0.1-degree grid so the cache hits more often
    return f"https://forecast.example/v2?lat={lat}&lon={lon}"
