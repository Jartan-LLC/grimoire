"""When to sow."""

from datetime import date, timedelta

from plantkit.model import CATALOG, Garden


def sow_dates(garden: Garden) -> list[tuple[date, str]]:
    """Each plant once, with its sowing date, by date then name."""
    names = {name for plants in garden.beds.values() for name in plants}
    return sorted((garden.last_frost - timedelta(weeks=CATALOG[name].sow_weeks), name) for name in names)
