# spellbook

A spell checker for Markdown documentation.

## Spec

- **Dictionaries** (`spellbook.dictionary`): load word lists (one word per line, `#` comments,
  optional frequency after a tab) from the bundled English list and any project lists named in
  `.spellbook`; matching ignores case except for words listed with a capital.
- **Suggestions** (`spellbook.suggest`): up to 5 candidates within Damerau-Levenshtein distance 2,
  ranked by distance, then by frequency.
- **Checker** (`spellbook.check`): finds misspelled words in a Markdown file, skipping fenced and
  inline code, URLs, and link targets; reports line and column.
- **Command** (`spellbook.cli`): `spellbook [--json] FILE...`, exit status 1 when anything is
  misspelled.
