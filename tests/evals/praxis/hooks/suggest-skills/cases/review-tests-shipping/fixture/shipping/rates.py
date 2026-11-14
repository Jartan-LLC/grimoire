"""Shipping rates by weight and zone."""

from decimal import Decimal

# Price per started kilogram, by zone.
PER_KG = {"domestic": Decimal("1.20"), "eu": Decimal("2.50"), "world": Decimal("6.00")}
FREE_FROM = Decimal("50.00")


def rate(weight_g: int, zone: str, order_total: Decimal) -> Decimal:
    """The shipping charge for a parcel of `weight_g` grams to `zone`."""
    if weight_g <= 0:
        raise ValueError(f"weight must be positive, got {weight_g}")
    if zone == "domestic" and order_total >= FREE_FROM:
        return Decimal("0.00")
    kilos = -(-weight_g // 1000)
    return PER_KG[zone] * kilos
