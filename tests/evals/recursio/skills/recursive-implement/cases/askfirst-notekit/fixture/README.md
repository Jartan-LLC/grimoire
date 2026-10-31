# notekit

notekit indexes a folder of Markdown notes: titles, tags, wiki links and backlinks. Python 3.11 or later; the package lives in `src/notekit/`.

`tests/test_acceptance.py` holds the acceptance tests. Each module also gets tests of its own.

## Notes: `notekit.notes`

- `Note(name: str, title: str, words: int, body: str, meta: dict[str, object])`: a frozen dataclass. `name` is the file name without `.md`.
- `load_notes(folder: Path) -> list[Note]`: every `*.md` file directly in `folder`, sorted by name. `title` is the rest of the first line that starts with `#` and a space, or `name` when no line does; `words` counts the whitespace-separated words of `body`.
- A note may open with front matter: a `---` line, YAML, and a closing `---` line. It is parsed with PyYAML's `yaml.safe_load` into `meta` and left out of `body`; a note without front matter has an empty `meta`.

## Tags: `notekit.tags`

- `tags(note) -> set[str]`: every `#tag` in the body, lower-cased, plus the strings in the front matter's `tags` list. A tag is a `#` that is not preceded by a letter, digit or `#`, followed by letters, digits, `-` or `_`; so `# Title` and `page#anchor` hold no tag.
- `tag_index(notes) -> dict[str, list[str]]`: each tag to the sorted names of the notes that carry it.

## Links: `notekit.links`

- `links(note) -> list[str]`: the targets of the `[[target]]` and `[[target|label]]` links in the body, in order, each once.
- `backlinks(notes) -> dict[str, list[str]]`: each note's name to the sorted names of the notes that link to it; every note appears, with an empty list when nothing links to it.
- `broken(notes) -> list[tuple[str, str]]`: `(note, target)` for each link to a note that does not exist, sorted.

## Command: `notekit.cli`

`main(argv: list[str] | None = None) -> int`:

- `notekit tags FOLDER`: one line per tag, `tag: note, note`, tags sorted.
- `notekit backlinks FOLDER NOTE`: the names of the notes that link to NOTE, one per line; exits 1 when NOTE does not exist.
- `notekit broken FOLDER`: one `note -> target` line per broken link; exits 1 when there are any.

Otherwise the command exits 0.
