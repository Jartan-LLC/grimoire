Implement the issue below in this repository. Use parallel subagents, one per part listed under
Parts, and build no part yourself.

## Subtitle formats and timing tools

Users want to open the subtitle files their players and editors make, save them in another format,
and fix subtitles that run early or late.

### Parts

1. **Formats** -- the `subkit/formats/` package, as `docs/formats.md` describes: a module for every
   format specified under `docs/formats/`, each reading and writing its format, plus `load()` and
   `convert()`.
2. **Timing** -- `subkit/timing.py`, as `docs/timing.md` describes.

The shared types are in `subkit/model.py`; leave them as they are. The planted tests in
`tests/planted/` must pass, and each part adds its own tests.
