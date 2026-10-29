"""Recipe files: a `# Title` line, a `serves: N` line, then one ingredient per line."""

from dataclasses import dataclass
from pathlib import Path

from pantry.quantity import format_quantity, parse_quantity


@dataclass
class Recipe:
    """A parsed recipe file."""

    title: str
    serves: int
    ingredients: list[tuple[float, str]]


def parse_line(line: str) -> tuple[float, str]:
    """Split "1 1/2 cup flour" into (1.5, "cup flour")."""
    parts = line.split()
    count = 2 if len(parts) > 2 and "/" in parts[1] else 1
    return parse_quantity(" ".join(parts[:count])), " ".join(parts[count:])


def load(path: Path) -> Recipe:
    """Read one recipe file."""
    lines = [line for line in path.read_text().splitlines() if line.strip()]
    title = lines[0].removeprefix("# ")
    serves = int(lines[1].removeprefix("serves:").strip())
    return Recipe(title, serves, [parse_line(line) for line in lines[2:]])


def render(recipe: Recipe) -> str:
    """The recipe as `pantry show` prints it."""
    out = [recipe.title, f"Serves {recipe.serves}", ""]
    out += [f"  {format_quantity(amount)} {rest}" for amount, rest in recipe.ingredients]
    return "\n".join(out)
