"""How much to water each bed."""

from datetime import date, timedelta

from plantkit.model import CATALOG, Garden, GardenError


def weekly_water(garden: Garden, rain: dict[date, float], week: date) -> dict[str, float]:
    """Each bed's water need for the week from Monday `week`, less that week's rain."""
    if week.weekday() != 0:
        raise GardenError(f"{week.isoformat()} is not a Monday")
    fallen = sum(rain.get(week + timedelta(days=n), 0.0) for n in range(7))
    return {
        bed: max(0.0, sum(CATALOG[name].water_mm for name in plants) - fallen)
        for bed, plants in garden.beds.items()
    }
