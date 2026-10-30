# textstats

Statistics for plain-text documents, as a library and a command.

## What it does

- **Tokenizer** (`textstats.tokenize`): split text into sentences and words. Abbreviations such
  as "e.g." and "Dr." do not end a sentence; hyphenated words and contractions stay one word.
- **Statistics** (`textstats.stats`): word count, unique words, the 10 most frequent words
  (ignoring a stop-word list), average sentence length, and the Flesch reading-ease score, with
  syllables counted by a vowel-group heuristic.
- **Reports** (`textstats.report`): render the statistics as plain text, JSON or a Markdown table.
- **Command** (`textstats.cli`): `textstats [--format text|json|markdown] FILE...`, reading stdin
  when no file is given, one report per file, exit status 2 on a file it cannot read.

## Status

Only the package skeleton exists.
