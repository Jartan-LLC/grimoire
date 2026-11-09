"""Stock by SKU and location."""

from collections import defaultdict


class Stock:
    """Quantities by SKU, each split across locations."""

    def __init__(self):
        self._by_sku = defaultdict(dict)

    def add(self, sku, location, quantity):
        """Add `quantity` of `sku` at `location`."""
        here = self._by_sku[sku]
        here[location] = here.get(location, 0) + quantity

    def total(self, sku):
        """All of `sku`, across locations."""
        return sum(self._by_sku.get(sku, {}).values())

    def lowest(self, n, skus=None):
        """The `n` SKUs with the least stock, fewest first."""
        names = skus if skus is not None else list(self._by_sku)
        return sorted(names, key=self.total)[:n]


def group_by_location(items):
    """Map each location to the (sku, quantity) pairs held there."""
    grouped = defaultdict(list)
    for sku, location, quantity in items:
        grouped[location].append((sku, quantity))
    return dict(grouped)
