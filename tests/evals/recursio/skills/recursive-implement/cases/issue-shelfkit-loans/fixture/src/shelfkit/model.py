"""The library's data model and its JSON file."""

import json
from dataclasses import dataclass, field
from datetime import date
from decimal import Decimal
from pathlib import Path


@dataclass(frozen=True)
class Book:
    isbn: str
    title: str
    price: Decimal


@dataclass(frozen=True)
class Member:
    id: str
    name: str
    limit: int


@dataclass(frozen=True)
class Loan:
    isbn: str
    member: str
    out: date
    due: date
    back: date | None = None


class LoanError(Exception):
    """A loan that cannot be made or closed."""


@dataclass
class Library:
    books: dict[str, Book] = field(default_factory=dict)
    members: dict[str, Member] = field(default_factory=dict)
    loans: list[Loan] = field(default_factory=list)


def _day(text: str | None) -> date | None:
    return date.fromisoformat(text) if text else None


def load(path: str | Path) -> Library:
    data = json.loads(Path(path).read_text())
    return Library(
        {b["isbn"]: Book(b["isbn"], b["title"], Decimal(b["price"])) for b in data["books"]},
        {m["id"]: Member(m["id"], m["name"], m["limit"]) for m in data["members"]},
        [
            Loan(n["isbn"], n["member"], date.fromisoformat(n["out"]), date.fromisoformat(n["due"]), _day(n.get("back")))
            for n in data["loans"]
        ],
    )


def save(library: Library, path: str | Path) -> None:
    data = {
        "books": [{"isbn": b.isbn, "title": b.title, "price": str(b.price)} for b in library.books.values()],
        "members": [{"id": m.id, "name": m.name, "limit": m.limit} for m in library.members.values()],
        "loans": [
            {
                "isbn": n.isbn,
                "member": n.member,
                "out": n.out.isoformat(),
                "due": n.due.isoformat(),
                "back": n.back.isoformat() if n.back else None,
            }
            for n in library.loans
        ],
    }
    Path(path).write_text(json.dumps(data, indent=2) + "\n")
