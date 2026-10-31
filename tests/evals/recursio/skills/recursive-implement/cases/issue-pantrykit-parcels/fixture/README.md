# pantrykit

pantrykit keeps the stock of a food bank's pantry and packs the weekly parcels for the households it serves. It is TypeScript that Node 24 or later runs directly, with no dependencies and no build step: the source lives in `src/`, the tests in `test/`, and `node --test` runs them. Relative imports name the `.ts` file. Dates are written `YYYY-MM-DD`; stock is counted in whole units.

`test/acceptance.test.ts` holds the acceptance tests. Each module also gets tests of its own.

## Data model: `src/model.ts`

- `Item = { name, kind: 'use-by' | 'best-before' }`, `Lot = { id, sku, qty, date }`, `Household = { id, name, size }` and `Pantry = { items, lots, households }`. `items` maps each SKU to its item. A lot is `qty` units of one SKU that share the date printed on the pack, a use-by or a best-before date as the item's `kind` says. `size` counts the people in a household.
- `PantryError`: a request that cannot be met.
- `parsePantry(text)` and `formatPantry(pantry)` read and write the pantry's JSON file; `addDays(date, n)` does date arithmetic and `checkDate(date)` throws `PantryError` for a date that is not a real `YYYY-MM-DD`.

## Stock: `src/stock.ts`

- `receive(pantry, sku, qty, date): Lot`: adds a lot and returns it. Its id is `l` and one more than the highest number among the pantry's lot ids. Throws `PantryError` when the SKU is unknown, `qty` is not a whole number above 0, or the date is not a real date.
- A lot whose date is `today` or later can be handed out; a use-by lot past its date cannot. Whether a best-before lot past its date can still be handed out has not been settled yet.
- `onHand(pantry, sku, today): number`: the units of the SKU that can be handed out on `today`.
- `take(pantry, sku, qty, today): Lot[]`: takes `qty` units from the lots that can be handed out, the earliest date first and, on the same date, the lot listed first. It lowers each lot's `qty`, removes a lot it empties, and returns what it took from each lot as `{ id, sku, qty, date }`. When fewer than `qty` units can be handed out, it throws `PantryError` naming the SKU and leaves the pantry as it was.

## Parcels: `src/parcels.ts`

- `TEMPLATE = { rice: 1, beans: 2, oats: 1, milk: 2 }`: units of each SKU per person.
- `parcelFor(size, template = TEMPLATE): Record<string, number>`: each SKU's units for a household of `size` people, in the template's order: the template's units times the size, counting at most 6 people.
- `pack(pantry, household, today, template = TEMPLATE): Lot[]`: takes the household's parcel from stock and returns every portion taken, in the template's order. Throws `PantryError` for an unknown household id, or naming the first SKU that is short; either way the pantry is left as it was, the SKUs that were not short included.

## Expiry: `src/expiry.ts`

- `expiring(pantry, today, days): Lot[]`: the lots whose date falls from `today` through `days` days after it, the earliest date first and the listed order kept on the same date.
- `summary(pantry, today, days): { sku, name, qty, date }[]`: one entry per SKU with lots in that window, giving the units in them and the earliest of their dates, ordered by that date and then by SKU.

## Command: `src/cli.ts`

`run(argv, files): { status, output, error }` runs the `pantrykit` command without touching the process, reading and writing the pantry file through `files = { read(path), write(path, text) }`; `bin/pantrykit.ts` wires it to the file system and the process.

- `pantrykit receive PANTRY SKU QTY DATE`: receives the lot, saves the pantry and prints `received <id>: <name> x<qty>, <kind> <date>`.
- `pantrykit pack PANTRY HOUSEHOLD TODAY`: packs the household's parcel, saves the pantry and prints one line per portion, `<name> x<qty> from <lot id>`, then `packed for <household name>`.
- `pantrykit expiring PANTRY TODAY DAYS`: one line per lot, `<date> <id> <name> x<qty>`, or `nothing expiring` when there is none.

The status is 0 on success. A `PantryError`, a file that cannot be read or a bad command line sets status 1 and the error `pantrykit: <message>` with a newline, and leaves the pantry file as it was.
