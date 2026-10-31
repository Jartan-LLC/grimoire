"""Plants, gardens and the garden file."""

import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path


class GardenError(Exception):
    """A garden, rain file or request that cannot be used."""


@dataclass(frozen=True)
class Plant:
    name: str
    family: str
    sow_weeks: int
    water_mm: float


CATALOG = {
    plant.name: plant
    for plant in (
        Plant("tomato", "nightshade", 6, 25.0),
        Plant("pepper", "nightshade", 8, 20.0),
        Plant("onion", "allium", 10, 10.0),
        Plant("garlic", "allium", 0, 8.0),
        Plant("bean", "legume", 2, 15.0),
        Plant("pea", "legume", 4, 12.0),
        Plant("kale", "brassica", 4, 18.0),
        Plant("cabbage", "brassica", 5, 20.0),
        Plant("carrot", "umbellifer", 3, 10.0),
    )
}


@dataclass(frozen=True)
class Garden:
    name: str
    last_frost: date
    first_frost: date
    beds: dict[str, list[str]]


def load_garden(path: str | Path) -> Garden:
    """Read a garden from its TOML file."""
    try:
        data = tomllib.loads(Path(path).read_text())
        garden = Garden(data["name"], data["last_frost"], data["first_frost"], dict(data["beds"]))
    except (KeyError, TypeError, tomllib.TOMLDecodeError) as error:
        raise GardenError(f"{path}: not a garden file ({error})") from error
    for bed, plants in garden.beds.items():
        for name in plants:
            if name not in CATALOG:
                raise GardenError(f"{path}: bed {bed}: unknown plant {name!r}")
    return garden
