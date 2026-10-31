"""Swap weeks between people, or hand one over."""

from dataclasses import replace
from datetime import date

from rotakit.model import Person, Rota, RotaError, Week

__all__ = ["give", "swap"]


def _index(rota: Rota, week: date) -> int:
    for index, held in enumerate(rota.weeks):
        if held.start == week:
            return index
    raise RotaError(f"no week starts on {week.isoformat()}")


def _person(rota: Rota, person: str) -> Person:
    for candidate in rota.people:
        if candidate.id == person:
            return candidate
    raise RotaError(f"unknown person {person!r}")


def _check_free(rota: Rota, person: str, week: date) -> None:
    if week in _person(rota, person).away:
        raise RotaError(f"{person} is away in the week of {week.isoformat()}")


def swap(rota: Rota, first: date, second: date) -> Rota:
    """A new rota with the people of the two weeks exchanged."""
    i, j = _index(rota, first), _index(rota, second)
    a, b = rota.weeks[i].person, rota.weeks[j].person
    _check_free(rota, a, second)
    _check_free(rota, b, first)
    weeks = list(rota.weeks)
    weeks[i], weeks[j] = Week(first, b), Week(second, a)
    return replace(rota, weeks=weeks)


def give(rota: Rota, week: date, person: str) -> Rota:
    """A new rota with the week handed to `person`."""
    index = _index(rota, week)
    _check_free(rota, person, week)
    weeks = list(rota.weeks)
    weeks[index] = Week(week, person)
    return replace(rota, weeks=weeks)
