"""The data model: people, weeks on call and the rota, kept as JSON."""

import json
from dataclasses import dataclass
from datetime import date
from pathlib import Path

__all__ = ["Person", "Rota", "RotaError", "Week", "load", "save"]


class RotaError(Exception):
    """A rota change that cannot be made."""


@dataclass(frozen=True)
class Person:
    id: str
    name: str
    away: tuple[date, ...] = ()


@dataclass(frozen=True)
class Week:
    start: date
    person: str


@dataclass
class Rota:
    people: list[Person]
    weeks: list[Week]


def load(path: str | Path) -> Rota:
    """Read a rota from its JSON file."""
    data = json.loads(Path(path).read_text())
    people = [
        Person(p["id"], p["name"], tuple(date.fromisoformat(d) for d in p.get("away", [])))
        for p in data["people"]
    ]
    weeks = [Week(date.fromisoformat(w["start"]), w["person"]) for w in data["weeks"]]
    return Rota(people, weeks)


def save(rota: Rota, path: str | Path) -> None:
    """Write a rota to its JSON file."""
    data = {
        "people": [
            {"id": p.id, "name": p.name, "away": [d.isoformat() for d in p.away]}
            for p in rota.people
        ],
        "weeks": [{"start": w.start.isoformat(), "person": w.person} for w in rota.weeks],
    }
    Path(path).write_text(json.dumps(data, indent=2) + "\n")
