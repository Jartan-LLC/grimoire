import sys
import pathlib

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "src"))

from weather.units import to_fahrenheit


def test_freezing():
    assert to_fahrenheit(0) == 32
