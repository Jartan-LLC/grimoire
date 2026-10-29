"""Read the DS18B20 sensor through the 1-Wire bus."""

from pathlib import Path

DEVICE = Path("/sys/bus/w1/devices/28-0000075a3c2f/w1_slave")


def parse_celsius(raw: str) -> float:
    """The temperature in a w1_slave reading, which ends in t=<millidegrees>."""
    return int(raw.rsplit("t=", 1)[1]) / 1000


def read_celsius(device: Path = DEVICE) -> float:
    """The current temperature in degrees Celsius."""
    return parse_celsius(device.read_text())
