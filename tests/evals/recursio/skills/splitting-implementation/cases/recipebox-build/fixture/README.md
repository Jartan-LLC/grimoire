# recipebox

Reads recipes written as plain text, scales them, works out their nutrition, and makes one shopping
list from several of them, as an ES-module library and a command. No dependencies; Node 24.

## Types

`src/types.js` holds the JSDoc types the modules pass to one another, `Rational`, `Quantity`,
`Ingredient`, `Recipe` and `NutrientRow`, and the `UNITS` table: the canonical unit names, what each
measures, and its size in millilitres or grams. Each module below uses these and nothing of its
siblings; only the command joins them.

## Parsing (`src/parse.js`)

- `parseQuantity(text)` returns a `Quantity` or null for text that is not one. Forms: `2`, `1/2`,
  `1 1/2` (a mixed number), `1.5` (an exact decimal, so `0.33` is 33/100), the words `a`, `an` and
  `one` (1), `half` (1/2), `a dozen` (12), and ranges `2-3`, `2 - 3`, `2 to 3` and `1/2-1`. Every
  fraction is reduced; a zero denominator, or a range whose low end is not below its high end, is
  null.
- `parseIngredient(line)` returns `{ ok: true, ingredient }` or `{ ok: false, message }`:
  - An optional quantity, then an optional unit, then the name. The unit may touch the number
    (`250g`, `2tbsp`) and a following `of` is dropped (`a pinch of salt`).
  - Unit aliases, case-insensitive except that `t` is tsp and `T` is tbsp, each with an optional
    trailing period and plural `s` or `es`: `tsp`, `teaspoon`; `tbsp`, `tbs`, `tablespoon`; `c`,
    `cup`; `fl oz`, `fluid ounce`; `pt`, `pint`; `qt`, `quart`; `gal`, `gallon`; `ml`,
    `millilitre`, `milliliter`; `l`, `litre`, `liter`; `oz`, `ounce`; `lb`, `lbs`, `pound`; `g`,
    `gram`; `kg`, `kilogram`; `pinch`; `dash`; `clove`; `can`. A word that is no alias is part of
    the name, and the ingredient is a count (`3 eggs`: unit null).
  - A parenthetical anywhere becomes the note (`1 (14 oz) can tomatoes`: 1 can, note `14 oz`), and
    so does the text after the first comma (`2 onions, finely chopped`). Both together are joined
    with a semicolon and a space.
  - A line ending in `to taste` has a null quantity and the note `to taste`
    (`salt and pepper to taste`); a bare name (`salt`) has a null quantity and unit.
  - The name is trimmed with inner spaces collapsed, case kept. An empty line is
    `empty line`; a quantity or unit with no name after it is `no ingredient name`.
- `parseRecipe(text)` returns `{ recipe, errors }`, errors as `{ line, message }` counted from 1:
  - The first non-blank line is the title, a leading `#` and its space removed.
  - `Serves 4`, `Servings: 4` or `Makes 12` sets the servings; with none the servings are 1 and
    the error `no servings line` is reported on line 1.
  - A line `Ingredients` (any case, with an optional colon or a leading `##`) starts the
    ingredients, and
    `Method`, `Directions`, `Steps` or `Instructions` starts the steps.
  - Among the ingredients, bullets `-`, `*` and `+` are stripped, and a line ending in `:` (or
    starting `For the`) is a section heading that every later ingredient carries until the next
    one. A bad ingredient line is an error and is skipped.
  - Steps lose a leading `1.` or `1)`. A blank line ends a step; the lines of one step join with
    a space.

## Units and scaling (`src/units.js`)

Arithmetic stays exact wherever it can: US volumes convert as whole ratios of teaspoons (tbsp 3,
floz 6, cup 48, pint 96, quart 192, gallon 768, pinch 1/16, dash 1/8), and masses within a system
as ratios too (lb 16 oz, kg 1000 g, l 1000 ml). Only a change of system goes through the `base`
sizes, and its result is rounded to the nearest 1/100 and held as a reduced rational.

- `add`, `mul`, `div` and `compare` on `Rational`s, each returning lowest terms.
- `convert(quantity, from, to, name)` converts both ends of a range. Volume to mass and back needs
  the density table, in grams per US cup, matched on the lower-cased name containing the key, the
  longest key winning: `flour` 120, `bread flour` 127, `sugar` 200, `brown sugar` 220,
  `powdered sugar` 120, `butter` 227, `rice` 185, `oats` 90, `cocoa` 85, `honey` 340, `milk` 245,
  `water` 236.6, `oil` 218. A name with no density, a count unit or a change between count and
  anything else throws a `RangeError` naming both units.
- `scale(ingredient, factor)` multiplies the quantity (both range ends) by a `Rational`; a null
  quantity stays null. `scaleRecipe(recipe, servings)` scales every ingredient by
  servings / recipe.servings and sets the new servings.
- `friendly(quantity, unit)` returns `{ quantity, unit, text }` in the unit a cook would use:
  - US volume except pinch and dash: work in teaspoons; 12 or more is cups, 3 or more is tbsp,
    otherwise tsp. The fractional part then rounds to the nearest of 0, 1/8, 1/4, 1/3, 1/2, 2/3,
    3/4 and 1, a tie going to the smaller; from 10 up the value rounds to a whole number. 9 tsp is
    `3 tbsp`, 12 tsp is `1/4 cup`, and 51 tsp is 1 1/16 cups, a tie, so `1 cup`.
  - Metric volume: below 1000 ml, ml rounded to the nearest 1 under 20 and the nearest 5 above;
    from 1000 ml, litres with up to two decimals and trailing zeros trimmed (`1.25 l`).
  - Metric mass the same way in g and kg, with the nearest 1 g under 100 and the nearest 5 above.
  - US mass: oz rounded to the nearest 1/4 below 16 oz, then lb rounded to the nearest 1/4.
  - Text writes a mixed number (`1 1/2`), then the unit: `cup`, `pint`, `quart`, `gallon`, `can`
    and `clove` take an `s` above 1; abbreviations never do. A range prints both ends with the
    unit once (`2-3 cups`). A count prints the number alone.
- `toSystem(ingredient, system)` converts an ingredient to `"us"` or `"metric"` (cup to ml, oz to
  g and back, picking the system's smallest unit and leaving the rest to `friendly`); counts and
  pinches stay as they are.

## Nutrition (`src/nutrition.js`)

- `loadTable(csvText)` reads the nutrient table: header
  `name,kcal,protein_g,fat_g,carbs_g,sodium_mg,grams_per_cup,grams_each`, values per 100 g, an
  empty cell for a null, `#` lines ignored. It returns `{ rows, errors }`; a row with a missing or
  non-numeric required cell is an error with its line number.
- `normaliseName(name)`: lower case, punctuation removed, the descriptors `fresh`, `large`,
  `medium`, `small`, `chopped`, `diced`, `minced`, `sliced`, `ground`, `unsalted` and `salted`
  dropped, and the last word made singular: `-ies` to `-y` (`berries`), `-oes` to `-o`
  (`tomatoes`), `-ves` to `-f` (`leaves`), and a final `s` dropped unless the word ends in `ss`.
- `match(name, rows)` finds the row for an ingredient: an exact match of normalised names first,
  then the row whose normalised name is the longest whole-word ending of the ingredient's (`red
  onion` finds `onion`), or null.
- `gramsOf(ingredient, row)`: mass units through `UNITS[unit].base`; volume units as base ml /
  236.5882365 x `row.gramsPerCup`; a count as the number x `row.gramsEach`; a `can` as 400 g, or
  the size its note gives (`14 oz`, `400 g`, `15.5 ounces`). A range uses its midpoint. Returns
  null when the row lacks what the unit needs.
- `nutrition(recipe, rows)` returns `{ perPortion, percentDaily, unmatched }`. `perPortion`
  totals kcal, protein, fat, carbohydrate and sodium over the ingredients and divides by the
  servings: kcal and mg as whole numbers, grams to one decimal. `percentDaily` divides by the daily values
  2000 kcal, 50 g protein, 78 g fat, 275 g carbohydrate and 2300 mg sodium, as whole percentages.
  An ingredient with a null quantity adds nothing and is not unmatched. `unmatched` lists
  `{ name, reason }` in recipe order, the reason one of `no match`, `no density` or
  `no piece weight`.

## Shopping list (`src/shopping.js`)

- `shoppingList(recipes, { pantry = [], aisles = AISLES } = {})` merges the ingredients of
  already-scaled recipes into `{ aisles: [{ aisle, items }], fromPantry }`.
- Items merge when their keys match: the name lower-cased, trimmed, with a final `s` or `es`
  dropped, plus the unit's dimension. Volume and mass of one item stay two items; counts merge by
  unit (`2 cloves` and `3 cloves`; `3 eggs` and `2 eggs`).
- When every line of an item shares one unit the amounts add exactly as rationals. Otherwise they
  add through `UNITS[unit].base`, and the total is shown in the largest unit used for which it is
  at least 1, as a decimal rounded to two places. Range ends add separately, and an exact amount
  adds to both ends. A line with a null quantity makes an item with no amount, and an amount
  added to it wins.
- `AISLES` lists, in order, Produce, Dairy and eggs, Bakery and baking, Meat and fish, Pantry,
  Spices and Other, each with keywords (Produce: onion, garlic, tomato, potato, carrot, lemon,
  lime, celery, pepper, herb, parsley, basil; Spices: salt, black pepper, cumin, paprika,
  cinnamon, chili, and so on). An item goes to the aisle of the longest keyword its name contains
  as whole words, so `black pepper` goes to Spices and `red pepper` to Produce; a tie goes to the
  earlier aisle; no keyword means Other. Aisles keep table order, empty ones left out, and items
  sort by name.
- A pantry entry removes an item whose name equals it or ends with it as a whole word (`salt`
  covers `sea salt`); removed items go to `fromPantry`, sorted.
- `renderList(list)` prints a `## Aisle` heading per aisle and `- 1 1/2 cups flour` per item,
  then `## Already in the pantry` if any; amounts as mixed numbers or the rounded decimal.

## Command (`bin/recipebox.js`)

- `recipebox scale FILE --servings N [--system us|metric]` prints the recipe scaled to N
  servings: title, `Serves N`, the ingredients under their sections with friendly amounts and
  notes after a comma, then the numbered steps.
- `recipebox shop FILE... [--servings N] [--pantry FILE]` scales every recipe to N servings when
  given, and prints the shopping list. The pantry file has one name per line.
- `recipebox nutrition FILE --table CSV [--servings N] [--json]` prints the per-serving table:
  one line per nutrient with amount and daily percentage, or the result as JSON with `--json`.
  Each unmatched ingredient prints to stderr as `warning: no nutrition for NAME (REASON)`.

Parse errors print to stderr as `FILE:LINE: message`. The exit status is 0, or 1 when any recipe
or table had errors, or 2 for a usage error or an unreadable file; other files are still read.

## Status

Only `src/types.js` exists.
