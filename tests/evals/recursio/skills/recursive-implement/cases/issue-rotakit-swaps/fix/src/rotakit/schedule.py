"""Plan the weeks of a rota."""

from datetime import date, timedelta

from rotakit.model import Person, RotaError, Week

__all__ = ["plan"]


def plan(people: list[Person], first: date, count: int) -> list[Week]:
    """`count` weeks from Monday `first`, taken in turn by whoever is not away."""
    if first.weekday() != 0:
        raise RotaError(f"{first.isoformat()} is not a Monday")
    weeks: list[Week] = []
    turn = 0
    for n in range(count):
        start = first + timedelta(weeks=n)
        for offset in range(len(people)):
            index = (turn + offset) % len(people)
            if start not in people[index].away:
                weeks.append(Week(start, people[index].id))
                turn = index + 1
                break
        else:
            raise RotaError(f"everyone is away in the week of {start.isoformat()}")
    return weeks
