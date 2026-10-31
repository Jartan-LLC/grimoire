# kennelkit

kennelkit runs the booking desk of a boarding kennel: bookings, prices and how full the runs are. It is TypeScript that Node 24 or later runs directly, with no dependencies and no build step: the source lives in `src/`, the tests in `test/`, and `node --test` runs them. Relative imports name the `.ts` file. Dates are written `YYYY-MM-DD`; money is held in whole cents.

`test/acceptance.test.ts` holds the acceptance tests. Each module also gets tests of its own.

## Data model: `src/model.ts`

- `Dog = { id, name, size: 'small' | 'large', vaccinatedUntil }`, `Booking = { id, dog, from, to }` and `Kennel = { runs: { small, large }, dogs, bookings }`. A booking holds the nights from `from` up to, but not including, `to`; `dog` is a dog's id; `runs` counts the kennel's runs of each size.
- `KennelError`: a booking or request that cannot be made.
- `parseKennel(text)` and `formatKennel(kennel)` read and write the kennel's JSON file; `addDays(date, n)` and `weekday(date)` (0 for Sunday) do date arithmetic.

## Bookings: `src/bookings.ts`

- `book(kennel, dog, from, to): Booking`: adds a booking and returns it. Its id is `b` and one more than the highest number among the kennel's booking ids. Throws `KennelError` when the dog is unknown, `to` is not after `from`, the dog already has a booking for one of those nights, or on one of them every run of the dog's size is taken.
- `cancel(kennel, id): Booking`: removes the booking and returns it; throws `KennelError` for an unknown id.

## Prices: `src/pricing.ts`

- `PRICES = { small: 3000, large: 4000 }`: cents per night by size.
- `price(booking, dog, prices = PRICES): number`: each night at the dog's size's price, plus 500 for each Friday and Saturday night; a stay of seven nights or more takes 10% off the whole, rounded down to whole cents.

## Occupancy: `src/occupancy.ts`

- `occupancy(kennel, from, to): Night[]`: one `{ date, small, large }` per night from `from` up to, but not including, `to`, counting the runs of each size taken that night.
- `busiest(kennel, from, to): Night | null`: the first of those nights with the most runs taken in all, or null when no run is taken.

## Command: `src/cli.ts`

`run(argv, files): { status, output, error }` runs the `kennelkit` command without touching the process, reading and writing the kennel file through `files = { read(path), write(path, text) }`; `bin/kennelkit.ts` wires it to the file system and the process.

- `kennelkit book KENNEL DOG FROM TO`: books the stay, saves the kennel and prints `booked <id>: <dog's name> <from> to <to>, <price with two decimals>`.
- `kennelkit cancel KENNEL ID`: cancels the booking, saves the kennel and prints `cancelled <id>`.
- `kennelkit occupancy KENNEL FROM TO`: one line per night, `<date> small <taken>/<runs> large <taken>/<runs>`.

The status is 0 on success. A `KennelError`, a file that cannot be read or a bad command line sets status 1 and the error `kennelkit: <message>` with a newline, and leaves the kennel file as it was.
