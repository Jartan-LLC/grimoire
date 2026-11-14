"""Read an orders file: `order_id,sku,quantity` per line."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Order:
    """One order line."""

    order_id: str
    sku: str
    quantity: int


def parse(line: str) -> Order:
    """The order on `line`."""
    order_id, sku, quantity = line.strip().split(",")
    count = int(quantity)
    if count <= 0:
        raise ValueError(f"quantity must be positive: {count}")
    return Order(order_id, sku, count)


def import_batch(lines: list[str]) -> list[Order]:
    """Every order in `lines`."""
    return [parse(line) for line in lines]
