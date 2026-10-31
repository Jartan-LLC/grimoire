"""The records the libcirc modules pass to one another."""

import datetime
import enum
from dataclasses import dataclass
from decimal import Decimal


class CircError(ValueError):
    """A request circulation refuses or input it cannot work with; the message says why."""


class ItemKind(enum.Enum):
    """What sort of item a barcode is on."""

    BOOK = "book"
    DVD = "dvd"
    REFERENCE = "reference"


class PatronKind(enum.Enum):
    """The patron's card type."""

    ADULT = "adult"
    CHILD = "child"


@dataclass(frozen=True)
class Item:
    """One copy on the shelf, known by its `barcode`."""

    barcode: str
    title: str
    kind: ItemKind


@dataclass(frozen=True)
class Patron:
    """A card holder."""

    id: str
    name: str
    kind: PatronKind = PatronKind.ADULT


@dataclass(frozen=True)
class Loan:
    """One item lent to one patron. `returned` is None while the item is out."""

    barcode: str
    patron: str
    out: datetime.date
    due: datetime.date
    returned: datetime.date | None = None
    renewals: int = 0


@dataclass(frozen=True)
class Hold:
    """A patron's place in the queue for a barcode."""

    barcode: str
    patron: str
    placed: datetime.datetime


@dataclass(frozen=True)
class Payment:
    """Money a patron paid toward fines."""

    patron: str
    day: datetime.date
    amount: Decimal
