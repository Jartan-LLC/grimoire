"""Unit conversions."""


def to_fahrenheit(celsius: float) -> float:
    """Celsius to Fahrenheit."""
    return celsius * 9 / 5 + 32
    # TODO: kelvin, once a provider sends it
