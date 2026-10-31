# brewkit

brewkit works out the numbers of a homebrew beer recipe: its gravity, alcohol, bitterness and colour, and the recipe scaled to another batch size. Python 3.11 or later, standard library only; the package lives in `src/brewkit/`. Units are metric.

`tests/test_acceptance.py` holds the acceptance tests. Each module also gets tests of its own.

## Recipes: `brewkit.recipe`

A recipe file holds one `key: value` per line; a `#` starts a comment, and blank lines are skipped.

```text
name: Garden Pale
batch: 20          # litres
efficiency: 72     # percent of the grain's extract that reaches the wort
grain: Pale malt, 4.5, 300, 3      # name, kg, potential, colour in degrees Lovibond
hop: Magnum, 20, 12.0, 60          # name, grams, alpha acid percent, minutes of boil
```

- `Grain(name: str, kg: float, potential: int, colour: float)`, `Hop(name: str, grams: float, alpha: float, minutes: int)` and `Recipe(name: str, batch: float, efficiency: float, grains: list[Grain], hops: list[Hop])`: dataclasses. `potential` is the gravity points one kilogram gives a litre of wort.
- `RecipeError(ValueError)`: a recipe that cannot be read.
- `parse_recipe(text: str) -> Recipe`: `grain` and `hop` lines may repeat, and keep their order. An unknown key, a line without `:`, a `grain` or `hop` with the wrong number of fields, or a number that does not parse raises `RecipeError` with a message that starts with `line N:` and a space. A recipe without `name`, `batch` or `efficiency` raises `RecipeError` naming the missing key.
- `format_recipe(recipe: Recipe) -> str`: the recipe as a file `parse_recipe` reads back: `name`, `batch` and `efficiency`, then each grain, then each hop, without comments. Kilograms take three decimals and grams one; every other number is written in its shortest form (`72`, `6.5`).

## Gravity and alcohol: `brewkit.gravity`

- `original_gravity(recipe) -> float`: 1 plus the grains' points, each `kg x potential x efficiency / 100`, summed, divided by the batch in litres and by 1000; rounded to three decimals.
- `final_gravity(og: float, attenuation: float) -> float`: `1 + (og - 1) x (1 - attenuation / 100)`, rounded to three decimals.
- `abv(og: float, fg: float) -> float`: the alcohol by volume, in percent, rounded to one decimal. Which formula it uses has not been settled yet: the simple `(og - fg) x 131.25`, or the alternate `76.08 x (og - fg) / (1.775 - og) x fg / 0.794`, which reads higher for strong beers.

## Bitterness: `brewkit.bitterness`

- `ibu(recipe, gravity: float) -> float`: Tinseth's formula, summed over the hops and rounded to one decimal. A hop's utilisation is `1.65 x 0.000125 ^ (gravity - 1) x (1 - e ^ (-0.04 x minutes)) / 4.15`, and it adds `utilisation x alpha / 100 x grams x 1000 / batch` IBU.

## Colour: `brewkit.colour`

- `srm(recipe) -> float`: Morey's formula, rounded to one decimal: the malt colour units `MCU = sum(colour x kg x 2.2046) / (batch x 0.2642)`, then `1.4922 x MCU ^ 0.6859`.
- `describe(srm: float) -> str`: `straw` below 4, `gold` below 8, `amber` below 15, `brown` below 25, otherwise `black`.

## Command: `brewkit.cli`

`main(argv: list[str] | None = None) -> int` runs the `brewkit` command.

- `brewkit stats RECIPE [--attenuation PCT]`: five lines, `og: 1.052`, `fg: 1.013`, `abv: 5.1%`, `ibu: 35.2` and `srm: 8.7 (amber)`. The final gravity uses the attenuation, 75 by default, and the bitterness the original gravity, both as printed.
- `brewkit scale RECIPE --batch LITRES`: prints the recipe for the new batch size, every grain's kilograms and every hop's grams scaled with it, as `format_recipe` writes it.

The exit status is 0 on success. A file that cannot be read or a `RecipeError` prints `brewkit: <message>` to stderr and exits 2.
