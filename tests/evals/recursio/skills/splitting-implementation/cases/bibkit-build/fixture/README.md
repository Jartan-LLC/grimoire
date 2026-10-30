# bibkit

Reads and writes bibliographies in BibTeX and RIS, formats them as reference lists in three
citation styles, and merges duplicate entries, as a library and a command.

## Data model

`src/bibkit/model.py` holds `Name` (given, von, family and jr parts), `EntryType`, `Entry` (key,
type, a dict of fields, authors and editors as `Name`s), `ParseError`, `ParseResult` (what both
readers return) and the `MONTHS` names. The docstrings there say how each value is stored. Every
module below works on these and on nothing else from its siblings; only the command uses them all.

## BibTeX (`bibkit.bibtex`)

`parse(text) -> ParseResult` returns the entries in file order, the `@preamble` strings and the
errors. An entry with a syntax error is reported and skipped, and parsing resumes at the next `@`.

- Entry types and field names are case-insensitive and stored in lower case. An entry may be
  delimited by braces or by parentheses: `@article{key, ...}` or `@article(key, ...)`. A trailing
  comma after the last field is allowed. Text outside entries is a comment and is ignored.
- `@string{jgr = "J. Geophys. Res."}` defines a macro, with a case-insensitive name. `@comment`
  is skipped entirely, braces and all. `@preamble{"..."}` adds its value to `preamble`.
- A value is a braced string, which may nest braces; a quoted string, which may hold braces and a
  quote inside braces (`"a {"} b"`); a bare number; or a macro name. Parts join with `#`:
  `jgr # " 112"` gives `J. Geophys. Res. 112`. An undefined macro is an error.
- `jan` to `dec` are predefined and expand to the full month names, so `month = sep` stores
  `September`. A numeric month from 1 to 12 is stored as its name too.
- Runs of whitespace, line breaks included, collapse to one space; the outer delimiters go but
  inner braces stay. A field given twice keeps the first value and reports an error; a key used
  twice is an error and the second entry is skipped.
- An unknown entry type is read as `MISC`.

`parse_names(value) -> list[Name]` splits a name list on the word `and` at brace depth 0, in any
case, and reads each name in one of BibTeX's three forms:

- `First von Last`: the von part is the run of words starting with a lower-case letter before the
  last word: `Johannes van der Waals`, `Ludwig van Beethoven`. With no lower-case word, the last
  word is the family name: `Mary Ann Smith`.
- `von Last, First`: `van der Waals, Johannes`.
- `von Last, Jr, First`: `King, Jr, Martin Luther`.
- A word in braces counts as one word and is never a particle: `{Barnes and Noble}` is one family
  name, and so is `{von Neumann}` in `John {von Neumann}`. Braces are removed in the stored parts.

`write(entries, preamble=()) -> str` writes entries in this canonical form, separated by blank
lines, after any `@preamble`s:

```bibtex
@article{waals1873,
  author = {van der Waals, Johannes and King, Jr, Martin Luther},
  title = {The {NASA} missions},
  journal = {Nature},
  month = sep,
  year = {1873},
}
```

Fields go `author`, `editor`, `title`, then the rest in alphabetical order. Names are written as
`von Last, Jr, First`, leaving out empty parts, and a month that is one of `MONTHS` is written as
its macro. For every list of entries the parser accepts, `parse(write(entries)).entries` equals
the list.

## RIS (`bibkit.ris`)

`read_ris(text) -> ParseResult` and `write_ris(entries) -> str`. A tag line is two capital letters
or a letter and a digit, two spaces, a hyphen and a space: `AU  - Smith, Jane`. A record runs from
`TY` to `ER`; a line that is not a tag line continues the previous value after one space. A tag
outside a record, or a record with no `ER` before the next `TY` or the end, is an error.

| RIS | Entry | Notes |
|-----|-------|-------|
| `TY` | type | `JOUR` article, `BOOK` book, `CHAP` incollection, `CONF` and `CPAPER` inproceedings, `RPRT` techreport, `ELEC` online, anything else misc |
| `AU`, `A1` | authors | `Last, First` or `Last, First, Suffix`, in order |
| `A2`, `ED` | editors | as authors |
| `TI`, `T1` | title | |
| `T2`, `JO`, `JF` | journal for `JOUR`, booktitle otherwise | the first of them present |
| `PY`, `DA` | year, month | `2020/05/17/`, `2020/05`, or `2020`; the month as its name |
| `VL`, `IS` | volume, number | |
| `SP`, `EP` | pages | `SP` and `EP` join as `112--119`; `SP` alone is the pages |
| `PB`, `CY` | publisher, address | |
| `DO`, `UR`, `SN` | doi, url, issn | |
| `AB`, `N1` | abstract, note | |
| `KW` | keywords | repeated tags joined by a semicolon and a space |

Other tags are ignored. Keys are made from the first author's family name in lower case with
everything but ASCII letters dropped, the year, and the first title word that is not `a`, `an` or
`the`, also lower case: `smith2020deep`. A key already taken gets `a`, `b` and so on appended. An
entry with no author uses `anon`, and one with no year uses `nodate`.

`write_ris` writes `TY`, the `AU` lines, `A2`, `TI`, `T2`, `PY` (`YYYY` or `YYYY/MM`), `VL`, `IS`,
`SP`, `EP`, `PB`, `CY`, `DO`, `UR`, `SN`, `AB`, `KW` (one line per keyword), `N1`, then an `ER`
line and a blank line. The types map back as `article` `JOUR`, `book` `BOOK`, `inbook` and
`incollection` `CHAP`, `inproceedings` `CPAPER`, `techreport` `RPRT`, `online` `ELEC`, and
`phdthesis`, `mastersthesis` and `misc` `GEN`. Inner braces are removed on the way out.

## Reference styles (`bibkit.styles`)

`format_reference(entry, style, suffix="") -> str` and `format_bibliography(entries, style) ->
list[str]` for the styles `apa`, `chicago` and `ieee`. Italics are marked with `*`, as in Markdown.
Braces are removed from every value, and the text inside them keeps its case whatever the style
does to the rest.

- **Initials**: each given name becomes its initial and a full stop, with a space between:
  `J. M.`; a hyphenated name keeps the hyphen: `Jean-Paul` gives `J.-P.`.
- **Title case** capitalises every word except `a`, `an`, `the`, `and`, `but`, `or`, `nor`, `for`,
  `as`, `at`, `by`, `in`, `of`, `on`, `per`, `to`, `up` and `via`, which stay lower case unless they
  are first, last or follow a colon. Both parts of a hyphenated word are capitalised.
- **Sentence case** lower-cases every word but the first, the first after a colon, and braced text.
- **APA 7**: authors `Family, G. M.` with `von` before the family name and `, Jr.` after the
  initials; two authors joined by a comma and an ampersand (`Smith, J., & Lee, K.`); three to
  twenty separated by commas, with the ampersand before the last; twenty-one or more as the
  first nineteen, `...`, and the last. Then `(Year).` or `(n.d.).`, the title in sentence case,
  then for an article the journal in title case and italics, `*volume*`, `(number)`, pages as
  `112-119`, and `https://doi.org/` plus the DOI when there is one. A book's title is in italics,
  followed by the publisher. Example:
  `Smith, J. M., & Lee, K. (2020). Deep sea vents. *Marine Geology*, *12*(3), 112-119.
  https://doi.org/10.1000/xyz`.
- **Chicago author-date**: the first author `Family, Given`, the rest `Given Family`, `and` before
  the last; with eleven or more, the first seven and `et al.` Then `Year.`, the title in title
  case, in double quotes for an article or chapter and in italics for a book, then the journal in
  italics, `volume (number): pages`.
- **IEEE**: authors `G. M. Family`, with `and` before the last of two or more and commas between;
  seven or more as the first author and `et al.` The title in title case and double quotes with a
  comma inside them, the journal in italics, then `vol. 12, no. 3, pp. 112-119, Sep. 2020.` Month
  names shorten to their first three letters and a full stop, except May, June and July.

`format_bibliography` sorts APA and Chicago by the first author's family name ignoring case and
`von`, then the other authors, then the year, then the title; entries with the same author list
and year get `a`, `b` and so on after the year in that order (`2020a`). IEEE keeps the input order
and numbers the references `[1]`, `[2]`. An entry with `others` among its authors is cited with
`et al.` after the listed ones in every style.

## Duplicates (`bibkit.dedupe`)

- `normalize_doi(value) -> str` lower-cases and strips `https://doi.org/`, `http://dx.doi.org/`
  and `doi:` prefixes and surrounding spaces: `DOI: 10.1000/ABC` gives `10.1000/abc`.
- `normalize_title(value) -> str` removes braces and the LaTeX accent commands (`{\"o}` gives `o`,
  `\'e` gives `e`), lower-cases, replaces every run of characters that are not letters or digits
  with one space, and trims.
- `find_duplicates(entries) -> list[list[int]]` groups the indexes of entries that match, where
  matching is transitive. Two entries match when both have DOIs and they normalise equal, or, when
  either lacks a DOI, their normalised titles have a Levenshtein ratio
  (1 - distance / longer length) of at least 0.92, their years are equal or both missing, and
  their first authors' family names are equal ignoring case and accents. Entries whose DOIs
  differ never match. Groups list indexes in ascending order and are sorted by their first index;
  entries with no duplicate are left out.
- `merge(entries) -> Entry` merges one group: the first entry's key; the type of the first entry
  that is not `MISC`; for each field, the longest value, the earlier entry winning a tie; the
  longest author and editor lists, the earlier winning a tie.
- `dedupe(entries) -> DedupeResult` holds the `entries` with each group replaced by its merge at
  the position of the group's first entry, and `merges`, one `Merge(kept, dropped, reason)` per
  group: the kept key, the dropped keys, and `doi` or `title`, whichever matched first.

## Command (`bibkit.cli`)

The input format follows the file extension: `.bib` is BibTeX and `.ris` is RIS.

- `bibkit format --style apa|chicago|ieee FILE...` reads every file, formats the entries together
  as one bibliography and prints one reference per line.
- `bibkit convert IN OUT` converts between the two formats; with the same extension on both it
  rewrites the file in canonical form.
- `bibkit dedupe [--output FILE] FILE...` merges the entries of all the files, writes them as
  BibTeX to `--output` or to stdout, and prints one line per merge to stderr:
  `merged smith2020deep <- smith2020deepa, jsmith20 (doi)`.

Parse errors print to stderr as `FILE:LINE: message` and the command carries on with what was
read, ending with status 1. A file that cannot be read or has another extension exits 2.

## Status

Only the data model exists.
