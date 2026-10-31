"""Plants that should not share a bed."""

from itertools import combinations

from plantkit.model import CATALOG, Garden

BAD_PAIRS = {frozenset({"allium", "legume"}), frozenset({"nightshade", "brassica"})}


def conflicts(garden: Garden) -> list[tuple[str, str, str]]:
    """(bed, plant, plant) for each two plants in one bed whose families clash."""
    found = [
        (bed, *sorted((a, b)))
        for bed, plants in garden.beds.items()
        for a, b in combinations(sorted(set(plants)), 2)
        if frozenset({CATALOG[a].family, CATALOG[b].family}) in BAD_PAIRS
    ]
    return sorted(found)
