Implement the issue below in this repository. Use parallel subagents, one per part listed under
Parts; build no part yourself.

## Bank imports and exports, and monthly reports

Users want to load their bank exports into ledgerkit, write transactions back out for other tools,
and see where the money went.

### Parts

1. **Importers** -- the `ledgerkit/importers/` package, as `docs/importers.md` describes: a module
   for every format specified under `docs/formats/`, each reading and writing its format, and
   `load()`.
2. **Reports** -- `ledgerkit/reports.py`, as `docs/reports.md` describes.

The shared types are in `ledgerkit/model.py`; leave them as they are. The planted tests in
`tests/planted/` must pass, and each part adds its own tests.
