"""The records the store keeps."""

from dataclasses import dataclass
from datetime import datetime


@dataclass
class Item:
    """One stocked product."""

    sku: str
    quantity: int
    # Timestamps are stored in UTC; convert to local time only when displaying them.
    updated: datetime
