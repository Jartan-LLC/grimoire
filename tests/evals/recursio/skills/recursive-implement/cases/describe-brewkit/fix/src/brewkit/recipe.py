# Copyright (c) 2026 The brewkit authors.
"""Read and write recipe files."""

from dataclasses import dataclass, field


class RecipeError(ValueError):
    """A recipe that cannot be read."""


@dataclass
class Grain:
    name: str
    kg: float
    potential: int
    colour: float


@dataclass
class Hop:
    name: str
    grams: float
    alpha: float
    minutes: int


@dataclass
class Recipe:
    name: str
    batch: float
    efficiency: float
    grains: list[Grain] = field(default_factory=list)
    hops: list[Hop] = field(default_factory=list)


def parse_recipe(text: str) -> Recipe:
    """The recipe in a recipe file."""
    values: dict[str, str] = {}
    grains: list[Grain] = []
    hops: list[Hop] = []
    for number, raw in enumerate(text.splitlines(), start=1):
        line = raw.split("#", 1)[0].strip()
        if not line:
            continue
        key, colon, value = line.partition(":")
        key, value = key.strip(), value.strip()
        try:
            if not colon:
                raise ValueError("expected 'key: value'")
            if key in ("name", "batch", "efficiency"):
                values[key] = value if key == "name" else str(float(value))
            elif key in ("grain", "hop"):
                fields = [f.strip() for f in value.split(",")]
                if len(fields) != 4:
                    raise ValueError(f"a {key} has 4 fields")
                if key == "grain":
                    grains.append(Grain(fields[0], float(fields[1]), int(fields[2]), float(fields[3])))
                else:
                    hops.append(Hop(fields[0], float(fields[1]), float(fields[2]), int(fields[3])))
            else:
                raise ValueError(f"unknown key {key!r}")
        except ValueError as error:
            raise RecipeError(f"line {number}: {error}") from error
    for key in ("name", "batch", "efficiency"):
        if key not in values:
            raise RecipeError(f"no {key}")
    return Recipe(values["name"], float(values["batch"]), float(values["efficiency"]), grains, hops)


def format_recipe(recipe: Recipe) -> str:
    """The recipe as a file parse_recipe reads back."""
    lines = [f"name: {recipe.name}", f"batch: {recipe.batch:g}", f"efficiency: {recipe.efficiency:g}"]
    lines += [f"grain: {g.name}, {g.kg:.3f}, {g.potential}, {g.colour:g}" for g in recipe.grains]
    lines += [f"hop: {h.name}, {h.grams:.1f}, {h.alpha:g}, {h.minutes}" for h in recipe.hops]
    return "".join(line + "\n" for line in lines)
